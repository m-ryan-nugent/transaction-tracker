"""Category schemas"""

from datetime import datetime

from typing import Optional, Literal

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base fields for categories."""
    name: str = Field(..., min_length=1, max_length=50)
    type: Literal["income", "expense", "transfer"]


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    type: Optional[Literal["income", "expense", "transfer"]] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    """Schema for category responses."""
    id: int
    name: str
    type: str
    is_system: bool
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    """Schema for list of categories."""
    categories: list[CategoryResponse]
    total: int
