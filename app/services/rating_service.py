
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions.custom_exceptions import (
    BlogNotFoundException,
    ResourceConflictException,
    ResourceNotFoundException,
)
from app.models.blog import Blog
from app.models.rating import Rating
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingUpdate


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


def create_rating(
    db: Session,
    blog_id: int,
    payload: RatingCreate,
    current_user: User,
) -> Rating:
   
    get_published_blog(blog_id, db)

    existing = db.scalar(
        select(Rating).where(
            Rating.blog_id == blog_id,
            Rating.user_id == current_user.id,
        )
    )

    if existing:
        raise ResourceConflictException(
            "You have already rated this blog; update your rating instead",
            "RATING_ALREADY_EXISTS",
        )

    rating = Rating(
        blog_id=blog_id,
        user_id=current_user.id,
        value=payload.value,
    )

    try:
        db.add(rating)
        db.commit()
        db.refresh(rating)
        return rating
    except IntegrityError:
        db.rollback()
        raise ResourceConflictException(
            "You have already rated this blog",
            "RATING_ALREADY_EXISTS",
        )
    except Exception:
        db.rollback()
        raise


def rating_summary(db: Session, blog_id: int) -> dict:
   
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


def my_rating(db: Session, blog_id: int, current_user: User) -> Rating:
   
    get_published_blog(blog_id, db)

    rating = db.scalar(
        select(Rating).where(
            Rating.blog_id == blog_id,
            Rating.user_id == current_user.id,
        )
    )

    if rating is None:
        raise ResourceNotFoundException(
            "You have not rated this blog",
            "RATING_NOT_FOUND",
        )

    return rating


def update_my_rating(
    db: Session,
    blog_id: int,
    payload: RatingUpdate,
    current_user: User,
) -> Rating:
   
    get_published_blog(blog_id, db)

    rating = db.scalar(
        select(Rating).where(
            Rating.blog_id == blog_id,
            Rating.user_id == current_user.id,
        )
    )

    if rating is None:
        raise ResourceNotFoundException(
            "You have not rated this blog",
            "RATING_NOT_FOUND",
        )

    rating.value = payload.value

    try:
        db.commit()
        db.refresh(rating)
        return rating
    except Exception:
        db.rollback()
        raise


def delete_my_rating(
    db: Session,
    blog_id: int,
    current_user: User,
) -> None:
   
    get_published_blog(blog_id, db)

    rating = db.scalar(
        select(Rating).where(
            Rating.blog_id == blog_id,
            Rating.user_id == current_user.id,
        )
    )

    if rating is None:
        raise ResourceNotFoundException(
            "You have not rated this blog",
            "RATING_NOT_FOUND",
        )

    try:
        db.delete(rating)
        db.commit()
    except Exception:
        db.rollback()
        raise
