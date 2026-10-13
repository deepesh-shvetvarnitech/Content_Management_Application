
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin


def register_user(db: Session, user_data: UserCreate) -> User:
    email = str(user_data.email).lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        raise ValueError("Email is already registered")

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


def authenticate_user(
    db: Session,
    credentials: UserLogin,
) -> User | None:
    email = str(credentials.email).lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None:
        return None

    if not verify_password(credentials.password, user.password_hash):
        return None

    if not user.is_active:
        return None

    return user
