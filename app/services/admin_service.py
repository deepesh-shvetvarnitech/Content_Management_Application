
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions.custom_exceptions import ResourceNotFoundException
from app.models.user import User


def list_users(db: Session) -> list[User]:
    
    return list(
        db.scalars(select(User).order_by(User.id)).all()
    )


def get_user(db: Session, user_id: int) -> User:
   
    user = db.get(User, user_id)

    if user is None:
        raise ResourceNotFoundException(
            "User not found",
            "USER_NOT_FOUND",
        )

    return user


def activate_user(db: Session, user_id: int) -> User:
  
    user = get_user(db, user_id)
    user.is_active = True

    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise


def deactivate_user(db: Session, user_id: int) -> User:
   
    user = get_user(db, user_id)
    user.is_active = False

    try:
        db.commit()
        db.refresh(user)
        return user
    except Exception:
        db.rollback()
        raise
