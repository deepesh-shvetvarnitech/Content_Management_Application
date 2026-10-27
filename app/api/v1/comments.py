

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from app.services.comment_service import (
    create_comment as create_comment_service,
    list_comments as list_comments_service,
    update_comment as update_comment_service,
    delete_comment as delete_comment_service,
)

router = APIRouter(prefix="/blogs", tags=["Comments"])


@router.post(
    "/{blog_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    blog_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_comment_service(db, blog_id, payload, current_user)


@router.get(
    "/{blog_id}/comments",
    response_model=list[CommentResponse],
)
def list_comments(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_comments_service(db, blog_id)


@router.put(
    "/{blog_id}/comments/{comment_id}",
    response_model=CommentResponse,
)
def update_comment(
    blog_id: int,
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_comment_service(
        db, blog_id, comment_id, payload, current_user
    )


@router.delete(
    "/{blog_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment(
    blog_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_comment_service(db, blog_id, comment_id, current_user)
