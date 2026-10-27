import logging

import jwt
from fastapi import HTTPException
from itsdangerous import BadSignature, SignatureExpired
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email_verification import verify_email_token
from app.core.exceptions.custom_exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    UserNotVerifiedException,
)
from app.core.redis_client import redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.models.user import User
from app.services.user_service import register_user, authenticate_user
from app.tasks.email_tasks import send_verification_email


logger = logging.getLogger(__name__)


def session_key(jti: str) -> str:
    return f"refresh:{jti}"


def refresh_ttl() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


def register_account(db: Session, user_data):
    try:
        user = register_user(db, user_data)
    except UserAlreadyExistsException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email is already registered",
        )

    try:
        send_verification_email.delay(user.id, user.email, user.name)
    except Exception:
        logger.exception(
            "Could not queue verification email for user_id=%s",
            user.id,
        )

    return user


def verify_account_email(db: Session, token: str) -> dict:
    try:
        payload = verify_email_token(token)
        user_id = int(payload["user_id"])
        email = str(payload["email"]).lower()
    except SignatureExpired:
        raise HTTPException(
            status_code=400,
            detail="Verification link has expired. Request a new email.",
        )
    except (BadSignature, ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=400,
            detail="Invalid verification link",
        )

    user = db.get(User, user_id)

    if user is None or user.email.lower() != email:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification link",
        )

    user.email_verified = True

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Email verified successfully"}


def login_account(db: Session, credentials) -> dict:
    user = authenticate_user(db, credentials)

    if user is None:
        raise InvalidCredentialsException()

    if not user.email_verified:
        raise UserNotVerifiedException()

    try:
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))
        payload = decode_refresh_token(refresh_token)

        redis_client.set(
            session_key(payload["jti"]),
            str(user.id),
            ex=refresh_ttl(),
        )
    except (RedisError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=503,
            detail="Authentication session service is unavailable",
        )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


ROTATE_REFRESH_SCRIPT = """
if redis.call('GET', KEYS[1]) ~= ARGV[1] then
    return 0
end
redis.call('DEL', KEYS[1])
redis.call('SET', KEYS[2], ARGV[1], 'EX', ARGV[2])
return 1
"""


LOGOUT_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


def refresh_account_token(db: Session, refresh_token: str) -> dict:
    try:
        payload = decode_refresh_token(refresh_token)
        user_id = int(payload["sub"])
        old_jti = payload["jti"]

        user = db.get(User, user_id)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="User not found or inactive",
            )

        new_refresh_token = create_refresh_token(str(user.id))
        new_payload = decode_refresh_token(new_refresh_token)

        rotated = redis_client.eval(
            ROTATE_REFRESH_SCRIPT,
            2,
            session_key(old_jti),
            session_key(new_payload["jti"]),
            str(user.id),
            str(refresh_ttl()),
        )

        if rotated != 1:
            raise HTTPException(
                status_code=401,
                detail="Refresh token is invalid or already used",
            )

        return {
            "access_token": create_access_token(str(user.id)),
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Authentication session service is unavailable",
        )


def logout_account(refresh_token: str) -> dict:
    try:
        payload = decode_refresh_token(refresh_token)

        revoked = redis_client.eval(
            LOGOUT_SCRIPT,
            1,
            session_key(payload["jti"]),
            str(payload["sub"]),
        )

        return {
            "message": "Logged out successfully",
            "revoked": bool(revoked),
        }

    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Authentication session service is unavailable",
        )
