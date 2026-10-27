
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.permissions import require_admin
from app.models.user import User
from app.schemas.blog import (
    BlogCreate,
    BlogPublishUpdate,
    BlogResponse,
    BlogUpdate,
)
from app.services.blog_service import (
    create_blog as create_blog_service,
    list_blogs as list_blogs_service,
    get_blog as get_blog_service,
    update_blog as update_blog_service,
    set_blog_published as set_blog_published_service,
    delete_blog as delete_blog_service,
)

router = APIRouter(prefix="/blogs", tags=["Blogs"])


@router.post(
    "/",
    response_model=BlogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_blog(
    payload: BlogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_blog_service(db, payload, current_user)


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
    return list_blogs_service(
        db=db,
        current_user=current_user,
        search=search,
        category_id=category_id,
        is_published=is_published,
        skip=skip,
        limit=limit,
    )


@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_blog_service(db, blog_id, current_user)


@router.patch("/{blog_id}", response_model=BlogResponse)
def update_blog(
    blog_id: int,
    payload: BlogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_blog_service(db, blog_id, payload, current_user)


@router.patch("/{blog_id}/publish", response_model=BlogResponse)
def set_blog_published(
    blog_id: int,
    payload: BlogPublishUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    return set_blog_published_service(db, blog_id, payload)


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog(
    blog_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    delete_blog_service(db, blog_id)
