from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.api.v1.users import require_admin


router = APIRouter(prefix="/categories", tags=["Categories"])

admin_router = APIRouter(
    prefix="/admin/categories",
    tags=["Categories"],
)


@admin_router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    existing = db.scalar(select(Category).where(Category.name == data.name))
    if existing:
        raise HTTPException(status_code=409, detail="Category already exists")

    category = Category(
        name=data.name,
        description=data.description,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@admin_router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    changes = data.model_dump(exclude_unset=True)

    if "name" in changes:
        if changes["name"] is None:
            raise HTTPException(status_code=422, detail="Category name cannot be null")

        if changes["name"] != category.name:
            existing = db.scalar(
                select(Category).where(Category.name == changes["name"])
            )
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Category name already exists",
                )

    for field, value in changes.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@admin_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.blogs:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete a category that has blogs",
        )

    db.delete(category)
    db.commit()
    return None
