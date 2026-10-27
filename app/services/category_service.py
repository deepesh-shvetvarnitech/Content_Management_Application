
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions.custom_exceptions import (
    CategoryNotFoundException,
    ResourceConflictException,
)
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def create_category(db: Session, data: CategoryCreate) -> Category:
   
    existing = db.scalar(
        select(Category).where(Category.name == data.name)
    )

    if existing:
        raise ResourceConflictException(
            "Category already exists",
            "CATEGORY_ALREADY_EXISTS",
        )

    
    category = Category(
        name=data.name,
        description=data.description,
    )

    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    except Exception:
        db.rollback()
        raise


def list_categories(db: Session) -> list[Category]:
   
    return list(
        db.scalars(
            select(Category).order_by(Category.name)
        ).all()
    )


def get_category(db: Session, category_id: int) -> Category:
    
    category = db.get(Category, category_id)

    if category is None:
        raise CategoryNotFoundException()

    return category


def update_category(
    db: Session,
    category_id: int,
    data: CategoryUpdate,
) -> Category:
    
    category = get_category(db, category_id)

    
    changes = data.model_dump(exclude_unset=True)

    if "name" in changes:
        if changes["name"] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Category name cannot be null",
            )

        if changes["name"] != category.name:
            existing = db.scalar(
                select(Category).where(
                    Category.name == changes["name"]
                )
            )

            if existing:
                raise ResourceConflictException(
                    "Category name already exists",
                    "CATEGORY_ALREADY_EXISTS",
                )

    
    for field, value in changes.items():
        setattr(category, field, value)

    try:
        db.commit()
        db.refresh(category)
        return category
    except Exception:
        db.rollback()
        raise


def delete_category(db: Session, category_id: int) -> None:
   
    category = get_category(db, category_id)

    
    if category.blogs:
        raise ResourceConflictException(
            "Cannot delete a category that has blogs",
            "CATEGORY_HAS_BLOGS",
        )

    try:
        db.delete(category)
        db.commit()
    except Exception:
        db.rollback()
        raise
