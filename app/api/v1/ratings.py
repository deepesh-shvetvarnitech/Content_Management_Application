
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.rating import (
    RatingCreate,
    RatingUpdate,
    RatingResponse,
    RatingSummary,
)
from app.services.rating_service import (
    create_rating as create_rating_service,
    rating_summary as rating_summary_service,
    my_rating as my_rating_service,
    update_my_rating as update_my_rating_service,
    delete_my_rating as delete_my_rating_service,
)

router = APIRouter(prefix="/blogs", tags=["Ratings"])


@router.post(
    "/{blog_id}/ratings",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rating(
    blog_id: int,
    payload: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_rating_service(db, blog_id, payload, current_user)


@router.get(
    "/{blog_id}/ratings/summary",
    response_model=RatingSummary,
)
def rating_summary(
    blog_id: int,
    db: Session = Depends(get_db),
):
    return rating_summary_service(db, blog_id)


@router.get(
    "/{blog_id}/ratings/me",
    response_model=RatingResponse,
)
def my_rating(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return my_rating_service(db, blog_id, current_user)


@router.put(
    "/{blog_id}/ratings/me",
    response_model=RatingResponse,
)
def update_my_rating(
    blog_id: int,
    payload: RatingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_my_rating_service(
        db, blog_id, payload, current_user
    )


@router.delete(
    "/{blog_id}/ratings/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_my_rating(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_my_rating_service(db, blog_id, current_user)
