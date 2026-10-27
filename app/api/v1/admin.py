
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.permissions import require_admin
from app.models.user import User
from app.schemas.user import AdminUserResponse

from app.services.admin_service import (
    list_users as list_users_service,
    get_user as get_user_service,
    activate_user as activate_user_service,
    deactivate_user as deactivate_user_service,
)

router = APIRouter(
    prefix="/admin/users",
    tags=["Admin User Management"],
)


@router.get("", response_model=list[AdminUserResponse])
def list_users(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return list_users_service(db)


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return get_user_service(db, user_id)


@router.patch("/{user_id}/activate", response_model=AdminUserResponse)
def activate_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return activate_user_service(db, user_id)


@router.patch("/{user_id}/deactivate", response_model=AdminUserResponse)
def deactivate_user(
    user_id: int,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # Admin apne hi account ko deactivate nahi kar sakta.
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot deactivate their own account",
        )

    return deactivate_user_service(db, user_id)

