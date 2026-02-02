"""Category routes."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_db, get_current_user
from app.api.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
)
from app.api.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Create a new category."""
    existing = await category_service.get_category_by_name(db, category.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists",
        )
    
    return await category_service.create_category(db, category)


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    type: Optional[str] = None,
    is_active: Optional[bool] = True,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """List all categories with optional filters."""
    return await category_service.get_all_categories(db, type, is_active)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Get a specific category by ID."""
    category = await category_service.get_category(db, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category: CategoryUpdate,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Update a category."""
    existing = await category_service.get_category(db, category_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    # Check for name conflict if updating name
    if category.name and category.name != existing.name:
        conflict = await category_service.get_category_by_name(db, category.name)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category with this name already exists",
            )
        
    return await category_service.update_category(db, category_id, category)
    

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db=Depends(get_db),
    _=Depends(get_current_user),
):
    """Delete a category."""
    deleted = await category_service.delete_category(db, category_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
