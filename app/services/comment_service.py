
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions.custom_exceptions import (
    BlogNotFoundException,
    CommentNotFoundException,
    ForbiddenException,
)
from app.models.blog import Blog
from app.models.comment import Comment
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate


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


def create_comment(
    db: Session,
    blog_id: int,
    payload: CommentCreate,
    current_user: User,
) -> Comment:
    
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

    try:
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment
    except Exception:
        db.rollback()
        raise


def list_comments(db: Session, blog_id: int) -> list[Comment]:
    """Published blog ke comments newest-first order mein return karein."""
    get_published_blog(blog_id, db)

    query = (
        select(Comment)
        .where(Comment.blog_id == blog_id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
    )
    return list(db.scalars(query).all())


def update_comment(
    db: Session,
    blog_id: int,
    comment_id: int,
    payload: CommentUpdate,
    current_user: User,
) -> Comment:
    """Sirf comment ka owner apna comment update kar sakta hai."""
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

    try:
        db.commit()
        db.refresh(comment)
        return comment
    except Exception:
        db.rollback()
        raise


def delete_comment(
    db: Session,
    blog_id: int,
    comment_id: int,
    current_user: User,
) -> None:
    
    comment = db.get(Comment, comment_id)

    if comment is None or comment.blog_id != blog_id:
        raise CommentNotFoundException()

    if current_user.role != "admin" and comment.user_id != current_user.id:
        raise ForbiddenException("You cannot delete another user comment")

    try:
        db.delete(comment)
        db.commit()
    except Exception:
        db.rollback()
        raise
