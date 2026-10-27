

import jwt
from itsdangerous import BadSignature, SignatureExpired

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email_verification import verify_email_token
from app.tasks.email_tasks import send_verification_email
from app.core.redis_client import redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.db.session import SessionLocal
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    UserProfileCreate,
    UserProfileResponse,
    UserUpdate,
    UserMeResponse,
)
from app.services.user_service import register_user, authenticate_user
from app.core.exceptions.custom_exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserNotVerifiedException,
    UserInactiveException,
    ForbiddenException,
)



from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["Authentication"])


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


def session_key(jti: str) -> str:
    return f"refresh:{jti}"


def refresh_ttl() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    try:
        
        user = register_user(db, user_data)

        
        try:
            send_verification_email.delay(
                user.id, user.email, user.name
            )
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "Could not queue verification email for user_id=%s",
                user.id,
            )

        return user
    except UserAlreadyExistsException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from exc


@router.get("/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    try:
        payload = verify_email_token(token)
        user_id = int(payload["user_id"])
        email = str(payload["email"]).lower()
    except SignatureExpired as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Request a new email.",
        ) from exc
    except (BadSignature, ValueError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link",
        ) from exc

    user = db.get(User, user_id)
    if user is None or user.email.lower() != email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link",
        )

    if not user.email_verified:
        user.email_verified = True
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    return {"message": "Email verified successfully"}


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, credentials)

    if user is None:
        raise InvalidCredentialsException()

    if not user.email_verified:
        raise UserNotVerifiedException()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    try:
        payload = decode_refresh_token(refresh_token)
        redis_client.set(
            session_key(payload["jti"]),
            str(user.id),
            ex=refresh_ttl(),
        )
    except (RedisError, jwt.InvalidTokenError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication session service is unavailable",
        ) from exc

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        payload = decode_refresh_token(body.refresh_token)
        user_id = int(payload["sub"])
        old_jti = payload["jti"]

        user = db.get(User, user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        new_refresh = create_refresh_token(str(user_id))
        new_payload = decode_refresh_token(new_refresh)

        rotated = redis_client.eval(
            ROTATE_REFRESH_SCRIPT,
            2,
            session_key(old_jti),
            session_key(new_payload["jti"]),
            str(user_id),
            refresh_ttl(),
        )

        if rotated != 1:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or already used",
            )

        return {
            "access_token": create_access_token(str(user_id)),
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication session service is unavailable",
        ) from exc


@router.post("/logout")
def logout(body: LogoutRequest):
    try:
        payload = decode_refresh_token(body.refresh_token)

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

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication session service is unavailable",
        ) from exc


