from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.exceptions.custom_exceptions import (
    BlogNotFoundException,
    CategoryNotFoundException,
    ForbiddenException,
)
from app.models.blog import Blog
from app.models.category import Category
from app.models.user import User
from app.schemas.blog import BlogCreate, BlogPublishUpdate, BlogUpdate


def create_blog(db: Session, payload: BlogCreate, current_user: User) -> Blog:
    category = db.get(Category, payload.category_id)
    if category is None:
        raise CategoryNotFoundException()

    blog = Blog(
        title=payload.title,
        content=payload.content,
        category_id=payload.category_id,
        author_id=current_user.id,
        is_published=False,
    )
    try:
        db.add(blog)
        db.commit()
        db.refresh(blog)
        return blog
    except Exception:
        db.rollback()
        raise


def list_blogs(
    db: Session,
    current_user: User,
    search: str | None = None,
    category_id: int | None = None,
    is_published: bool | None = None,
    skip: int = 0,
    limit: int = 10,
) -> list[Blog]:
    query = select(Blog)

    # Non-admin users see published blogs and their own drafts.
    if current_user.role != "admin":
        query = query.where(
            or_(
                Blog.is_published.is_(True),
                Blog.author_id == current_user.id,
            )
        )

    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(Blog.title.ilike(term), Blog.content.ilike(term))
        )

    if category_id is not None:
        query = query.where(Blog.category_id == category_id)

    if is_published is not None:
        query = query.where(Blog.is_published == is_published)

    query = query.order_by(Blog.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def get_blog(db: Session, blog_id: int, current_user: User) -> Blog:
    blog = db.get(Blog, blog_id)
    if blog is None:
        raise BlogNotFoundException()

    if (
        not blog.is_published
        and current_user.role != "admin"
        and blog.author_id != current_user.id
    ):
        raise ForbiddenException("Access denied")

    return blog


def update_blog(
    db: Session,
    blog_id: int,
    payload: BlogUpdate,
    current_user: User,
) -> Blog:
    blog = db.get(Blog, blog_id)
    if blog is None:
        raise BlogNotFoundException()

    if current_user.role != "admin" and blog.author_id != current_user.id:
        raise ForbiddenException("You cannot edit this blog")

    changes = payload.model_dump(exclude_unset=True)

    if "category_id" in changes:
        category = db.get(Category, changes["category_id"])
        if category is None:
            raise CategoryNotFoundException()

    for field, value in changes.items():
        setattr(blog, field, value)

    try:
        db.commit()
        db.refresh(blog)
        return blog
    except Exception:
        db.rollback()
        raise


def set_blog_published(
    db: Session,
    blog_id: int,
    payload: BlogPublishUpdate,
) -> Blog:
    blog = db.get(Blog, blog_id)
    if blog is None:
        raise BlogNotFoundException()

    blog.is_published = payload.is_published

    try:
        db.commit()
        db.refresh(blog)
        return blog
    except Exception:
        db.rollback()
        raise


def delete_blog(db: Session, blog_id: int) -> None:
    blog = db.get(Blog, blog_id)
    if blog is None:
        raise BlogNotFoundException()

    try:
        db.delete(blog)
        db.commit()
    except Exception:
        db.rollback()
        raise
