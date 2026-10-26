from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.blog import Blog
from app.core.exceptions.custom_exceptions import BlogNotFoundException, ResourceNotFoundException, ResourceConflictException
from app.models.rating import Rating
from app.models.user import User
from app.schemas.rating import (
    RatingCreate,
    RatingUpdate,
    RatingResponse,
    RatingSummary,
)

router = APIRouter(prefix="/blogs", tags=["Ratings"])


def get_published_blog(blog_id: int, db: Session) -> Blog:
    blog = db.get(Blog, blog_id)

    if blog is None:
        raise BlogNotFoundException()

    if not blog.is_published:
        raise HTTPException(
            status_code=400,
            detail="Ratings are allowed only on published blogs",
        )

    return blog


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
    get_published_blog(blog_id, db)

    existing = db.scalar(
        select(Rating).where(
            Rating.blog_id == blog_id,
            Rating.user_id == current_user.id,
        )
    )

    if existing:
        raise ResourceConflictException("You have already rated this blog; update your rating instead", "RATING_ALREADY_EXISTS")

    rating = Rating(
        blog_id=blog_id,
        user_id=current_user.id,
        value=payload.value,
    )
    db.add(rating)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ResourceConflictException("You have already rated this blog", "RATING_ALREADY_EXISTS")

    db.refresh(rating)
    return rating


@router.get(
    "/{blog_id}/ratings/summary",
    response_model=RatingSummary,
)
def rating_summary(
    blog_id: int,
    db: Session = Depends(get_db),
):
    get_published_blog(blog_id, db)

    average, total = db.execute(
        select(func.avg(Rating.value), func.count(Rating.id)).where(
            Rating.blog_id == blog_id
        )
    ).one()

    return {
        "blog_id": blog_id,
        "average_rating": round(float(average), 2) if average is not None else None,
        "total_ratings": total,
    }


@router.get(
    "/{blog_id}/ratings/me",
    response_model=RatingResponse,
)
def my_rating(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_published_blog(blog_id, db)

    rating = db.scalar(
        select(Rating).where(
            Rating.blog_id == blog_id,
            Rating.user_id == current_user.id,
        )
    )

    if rating is None:
        raise ResourceNotFoundException("You have not rated this blog", "RATING_NOT_FOUND")

    return rating


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
    get_published_blog(blog_id, db)

    rating = db.scalar(
        select(Rating).where(
            Rating.blog_id == blog_id,
            Rating.user_id == current_user.id,
        )
    )

    if rating is None:
        raise ResourceNotFoundException("You have not rated this blog", "RATING_NOT_FOUND")

    rating.value = payload.value
    db.commit()
    db.refresh(rating)
    return rating


@router.delete(
    "/{blog_id}/ratings/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_my_rating(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rating = db.scalar(
        select(Rating).where(
            Rating.blog_id == blog_id,
            Rating.user_id == current_user.id,
        )
    )

    if rating is None:
        raise ResourceNotFoundException("You have not rated this blog", "RATING_NOT_FOUND")

    db.delete(rating)
    db.commit()
