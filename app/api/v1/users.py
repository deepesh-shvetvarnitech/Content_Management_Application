

import jwt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
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
)
from app.services.user_service import register_user, authenticate_user


router = APIRouter(prefix="/users", tags=["Users"])
bearer_scheme = HTTPBearer(auto_error=False)


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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def session_key(jti: str) -> str:
    return f"refresh:{jti}"


def refresh_ttl() -> int:
    return settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please login and provide a Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# RBAC: Admin authorization dependency
def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


# RBAC: Admin-only test endpoint
@router.get("/admin/check")
def admin_check(
    current_admin: User = Depends(require_admin),
):
    return {
        "message": "Admin access granted",
        "user_id": current_admin.id,
        "role": current_admin.role,
    }


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
        # Public registration never accepts a role from the request.
        return register_user(db, user_data)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from exc


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, credentials)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

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


@router.post(
    "/me/profile",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(UserProfile).where(
            UserProfile.user_id == current_user.id
        )
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists. Use PUT to update it.",
        )

    profile = UserProfile(
        user_id=current_user.id,
        **profile_data.model_dump(),
    )

    db.add(profile)
    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return profile


@router.get(
    "/me/profile",
    response_model=UserProfileResponse,
)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.scalar(
        select(UserProfile).where(
            UserProfile.user_id == current_user.id
        )
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return profile


@router.put(
    "/me/profile",
    response_model=UserProfileResponse,
)
def update_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.scalar(
        select(UserProfile).where(
            UserProfile.user_id == current_user.id
        )
    )

    if profile is None:
        profile = UserProfile(
            user_id=current_user.id,
            **profile_data.model_dump(),
        )
        db.add(profile)
    else:
        for field, value in profile_data.model_dump(
            exclude_unset=True
        ).items():
            setattr(profile, field, value)

    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return profile