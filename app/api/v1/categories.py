
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.permissions import require_admin
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
)
from app.services.category_service import (
    create_category as create_category_service,
    list_categories as list_categories_service,
    get_category as get_category_service,
    update_category as update_category_service,
    delete_category as delete_category_service,
)


router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
)

admin_router = APIRouter(
    prefix="/admin/categories",
    tags=["Categories"],
)


@admin_router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    return create_category_service(db, data)


@router.get(
    "",
    response_model=list[CategoryResponse],
)
def list_categories(
    db: Session = Depends(get_db),
):
    return list_categories_service(db)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    return get_category_service(db, category_id)


@admin_router.put(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    return update_category_service(db, category_id, data)


@admin_router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    delete_category_service(db, category_id)
    return None
