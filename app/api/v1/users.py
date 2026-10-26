

from itsdangerous import BadSignature, SignatureExpired

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy import select
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_admin
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.user import (
    UserProfileCreate,
    UserProfileResponse,
    UserUpdate,
    UserMeResponse,
)


router = APIRouter(prefix="/users", tags=["Users"])
bearer_scheme = HTTPBearer(auto_error=False)

















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

@router.get("/me", response_model=UserMeResponse)
def get_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.scalar(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "bio": profile.bio if profile else None,
        "profile_image_url": profile.profile_picture if profile else None,
    }


@router.put("/me", response_model=UserMeResponse)
def update_my_account(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
        current_user.name = changes["name"]

    profile_fields = {
        "bio": changes.get("bio"),
        "profile_picture": changes.get("profile_image_url"),
    }
    fields_provided = (
        "bio" in changes or "profile_image_url" in changes
    )

    if fields_provided:
        profile = db.scalar(
            select(UserProfile).where(
                UserProfile.user_id == current_user.id
            )
        )
        if profile is None:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)

        if "bio" in changes:
            profile.bio = profile_fields["bio"]
        if "profile_image_url" in changes:
            profile.profile_picture = profile_fields["profile_picture"]

    try:
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        raise

    return get_my_account(current_user=current_user, db=db)
