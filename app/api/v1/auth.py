


from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
)
from app.services.auth_service import (
    register_account,
    verify_account_email,
    login_account,
    refresh_account_token,
    logout_account,
)



router = APIRouter(prefix="/users", tags=["Authentication"])



@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    return register_account(db, user_data)



@router.get("/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    return verify_account_email(db, token)



@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    return login_account(db, credentials)



@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    return refresh_account_token(db, body.refresh_token)



@router.post("/logout")
def logout(body: LogoutRequest):
    return logout_account(body.refresh_token)
