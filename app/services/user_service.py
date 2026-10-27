from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password
from app.core.exceptions.custom_exceptions import UserAlreadyExistsException
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.user import UserCreate, UserLogin, UserProfileCreate, UserUpdate


def register_user(db: Session, user_data: UserCreate) -> User:
    email = str(user_data.email).lower()

    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        raise UserAlreadyExistsException()

    user = User(
        name=user_data.name,
        email=email,
        password_hash=hash_password(user_data.password),
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return user


def authenticate_user(db: Session, credentials: UserLogin) -> User | None:
    email = str(credentials.email).lower()
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        return None
    if not verify_password(credentials.password, user.password_hash):
        return None
    if not user.is_active:
        return None

    return user


def create_user_profile(
    db: Session,
    user: User,
    profile_data: UserProfileCreate,
) -> UserProfile:
    existing = db.scalar(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists. Use PUT to update it.",
        )

    profile = UserProfile(
        user_id=user.id,
        **profile_data.model_dump(),
    )
    try:
        db.add(profile)
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return profile


def get_user_profile(db: Session, user: User) -> UserProfile:
    profile = db.scalar(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


def update_user_profile(
    db: Session,
    user: User,
    profile_data: UserProfileCreate,
) -> UserProfile:
    profile = db.scalar(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )

    if profile is None:
        profile = UserProfile(
            user_id=user.id,
            **profile_data.model_dump(),
        )
        db.add(profile)
    else:
        for field, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)

    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise

    return profile


def get_my_account(db: Session, user: User) -> dict:
    profile = db.scalar(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "bio": profile.bio if profile else None,
        "profile_image_url": profile.profile_picture if profile else None,
    }


def update_my_account(db: Session, user: User, payload: UserUpdate) -> dict:
    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one field to update",
        )

    if "name" in changes:
        if changes["name"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Name cannot be null",
            )
        user.name = changes["name"]

    fields_provided = "bio" in changes or "profile_image_url" in changes

    if fields_provided:
        profile = db.scalar(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        if profile is None:
            profile = UserProfile(user_id=user.id)
            db.add(profile)

        if "bio" in changes:
            profile.bio = changes["bio"]
        if "profile_image_url" in changes:
            profile.profile_picture = changes["profile_image_url"]

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return get_my_account(db=db, user=user)
