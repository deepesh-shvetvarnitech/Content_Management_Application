from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_admin
from app.db.session import get_db
from app.core.exceptions.custom_exceptions import (
    BlogNotFoundException,
    CategoryNotFoundException,
    ForbiddenException,
)
from app.models.blog import Blog
from app.models.category import Category
from app.models.user import User
from app.schemas.blog import (
    BlogCreate,
    BlogPublishUpdate,
    BlogResponse,
    BlogUpdate,
)

router = APIRouter(prefix="/blogs", tags=["Blogs"])


@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
def create_blog(
    payload: BlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return blog


@router.get("/", response_model=list[BlogResponse])
def list_blogs(
    search: str | None = Query(default=None, min_length=1, max_length=200),
    category_id: int | None = Query(default=None, gt=0),
    is_published: bool | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Blog)

    # Regular users see published blogs and their own drafts.
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


@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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


@router.patch("/{blog_id}", response_model=BlogResponse)
def update_blog(
    blog_id: int,
    payload: BlogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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

    db.commit()
    db.refresh(blog)
    return blog


@router.patch("/{blog_id}/publish", response_model=BlogResponse)
def set_blog_published(
    blog_id: int,
    payload: BlogPublishUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    blog = db.get(Blog, blog_id)
    if blog is None:
        raise BlogNotFoundException()

    blog.is_published = payload.is_published
    db.commit()
    db.refresh(blog)
    return blog


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    blog = db.get(Blog, blog_id)
    if blog is None:
        raise BlogNotFoundException()

    db.delete(blog)
    db.commit()
