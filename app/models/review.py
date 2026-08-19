from typing import Optional
from sqlmodel import Field, SQLModel

class ReviewBase(SQLModel):
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=1000)

class Review(ReviewBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    product_id: int = Field(foreign_key="product.id")

class ReviewCreate(ReviewBase):
    pass

class ReviewPublic(ReviewBase):
    id: int
    user_id: int
    product_id: int
