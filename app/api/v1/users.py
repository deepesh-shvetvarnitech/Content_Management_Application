
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_admin
from app.models.user import User
from app.schemas.user import (
    UserProfileCreate,
    UserProfileResponse,
    UserUpdate,
    UserMeResponse,
)
from app.services.user_service import (
    create_user_profile,
    get_user_profile,
    update_user_profile,
    get_my_account,
    update_my_account,
)

router = APIRouter(prefix="/users", tags=["Users"])



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
    return create_user_profile(db, current_user, profile_data)



@router.get(
    "/me/profile",
    response_model=UserProfileResponse,
)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_profile(db, current_user)



@router.put(
    "/me/profile",
    response_model=UserProfileResponse,
)
def update_profile(
    profile_data: UserProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_user_profile(db, current_user, profile_data)



@router.get("/me", response_model=UserMeResponse)
def get_my_account_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_my_account(db, current_user)



@router.put("/me", response_model=UserMeResponse)
def update_my_account_endpoint(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_my_account(db, current_user, payload)


