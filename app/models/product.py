from typing import Optional
from sqlmodel import Field, SQLModel

class ProductBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: float = Field(ge=0.0)
    stock: int = Field(default=0, ge=0)
    category_id: int = Field(foreign_key="category.id")

class Product(ProductBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ProductCreate(ProductBase):
    pass

class ProductPublic(ProductBase):
    id: int

class ProductUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    price: Optional[float] = Field(default=None, ge=0.0)
    stock: Optional[int] = Field(default=None, ge=0)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
