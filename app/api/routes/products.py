from typing import Any
from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep, CurrentUser
from app.models.product import ProductPublic, ProductCreate, ProductUpdate
from app.services import product_service

router = APIRouter()

@router.post("/", response_model=ProductPublic)
def create_product(*, session: SessionDep, current_user: CurrentUser, product_in: ProductCreate) -> Any:
    return product_service.create_product(session=session, product_in=product_in)

@router.get("/", response_model=list[ProductPublic])
def read_products(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    return product_service.get_products(session=session, skip=skip, limit=limit)

@router.get("/{product_id}", response_model=ProductPublic)
def read_product(product_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    product = product_service.get_product_by_id(session=session, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductPublic)
def update_product(product_id: int, product_in: ProductUpdate, session: SessionDep, current_user: CurrentUser) -> Any:
    product = product_service.get_product_by_id(session=session, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product_service.update_product(session=session, db_item=product, product_in=product_in)

@router.delete("/{product_id}")
def delete_product(product_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    product = product_service.get_product_by_id(session=session, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_service.delete_product(session=session, db_item=product)
    return {"message": "Product deleted successfully"}
