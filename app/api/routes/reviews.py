from typing import Any
from fastapi import APIRouter

from app.api.deps import SessionDep, CurrentUser
from app.models.review import ReviewPublic, ReviewCreate
from app.services import review_service

router = APIRouter()

@router.post("/{product_id}/reviews", response_model=ReviewPublic)
def create_review(product_id: int, *, session: SessionDep, current_user: CurrentUser, review_in: ReviewCreate) -> Any:
    return review_service.create_review(
        session=session,
        review_in=review_in,
        user_id=current_user.id,
        product_id=product_id
    )

@router.get("/{product_id}/reviews", response_model=list[ReviewPublic])
def read_reviews(product_id: int, session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    return review_service.get_reviews_by_product(session=session, product_id=product_id, skip=skip, limit=limit)
