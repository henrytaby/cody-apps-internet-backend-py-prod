from typing import Any
from fastapi import APIRouter

from app.api.deps import SessionDep, CurrentUser
from app.models.cart_item import CartItemPublic, CartItemCreate
from app.services import cart_service

router = APIRouter()

@router.post("/", response_model=CartItemPublic)
def add_to_cart(*, session: SessionDep, current_user: CurrentUser, cart_in: CartItemCreate) -> Any:
    return cart_service.add_to_cart(
        session=session,
        cart_in=cart_in,
        user_id=current_user.id
    )

@router.get("/", response_model=list[CartItemPublic])
def read_cart(session: SessionDep, current_user: CurrentUser) -> Any:
    return cart_service.get_cart(session=session, user_id=current_user.id)
