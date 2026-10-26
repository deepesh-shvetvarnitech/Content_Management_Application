from fastapi import Depends

from app.models.user import User
from app.dependencies.auth import get_current_user
from app.core.exceptions.custom_exceptions import ForbiddenException


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise ForbiddenException("Admin access required")

    return current_user
