from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.db.session import get_db
from app.models.blog import Blog
from app.core.exceptions.custom_exceptions import BlogNotFoundException, CommentNotFoundException, ForbiddenException
from app.models.comment import Comment
from app.models.user import User
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
)

router = APIRouter(prefix="/blogs", tags=["Comments"])


def get_published_blog(blog_id: int, db: Session) -> Blog:
    blog = db.get(Blog, blog_id)

    if blog is None:
        raise BlogNotFoundException()

    if not blog.is_published:
        raise HTTPException(
            status_code=400,
            detail="Comments are allowed only on published blogs",
        )

    return blog


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
    get_published_blog(blog_id, db)

    content = payload.content.strip()
    if not content:
        raise HTTPException(
            status_code=422,
            detail="Comment content cannot be empty",
        )

    comment = Comment(
        blog_id=blog_id,
        user_id=current_user.id,
        content=content,
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get(
    "/{blog_id}/comments",
    response_model=list[CommentResponse],
)
def list_comments(
    blog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_published_blog(blog_id, db)

    query = (
        select(Comment)
        .where(Comment.blog_id == blog_id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
    )

    return list(db.scalars(query).all())


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
    get_published_blog(blog_id, db)

    comment = db.get(Comment, comment_id)

    if comment is None or comment.blog_id != blog_id:
        raise CommentNotFoundException()

    if comment.user_id != current_user.id:
        raise ForbiddenException("You cannot edit another user comment")

    content = payload.content.strip()
    if not content:
        raise HTTPException(
            status_code=422,
            detail="Comment content cannot be empty",
        )

    comment.content = content
    db.commit()
    db.refresh(comment)
    return comment


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
    comment = db.get(Comment, comment_id)

    if comment is None or comment.blog_id != blog_id:
        raise CommentNotFoundException()

    if current_user.role != "admin" and comment.user_id != current_user.id:
        raise ForbiddenException("You cannot delete another user comment")

    db.delete(comment)
    db.commit()
