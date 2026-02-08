"""Category service"""

from typing import Optional
from datetime import datetime

import aiosqlite

from app.api.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
)


async def create_category(
    db: aiosqlite.Connection, category: CategoryCreate
) -> CategoryResponse:
    """Create a new category."""
    cursor = await db.execute(
        """
        INSERT INTO categories (name, type, is_system)
        VALUES (?, ?, 0)
        """,
        (category.name, category.type),
    )
    await db.commit()

    return await get_category(db, cursor.lastrowid)


async def get_category(
    db: aiosqlite.Connection, category_id: int
) -> Optional[CategoryResponse]:
    """Get a single category by ID."""
    cursor = await db.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    row = await cursor.fetchone()

    if not row:
        return None

    return _row_to_category_response(dict(row))


async def get_category_by_name(
    db: aiosqlite.Connection, name: str
) -> Optional[CategoryResponse]:
    """Get a category by name."""
    cursor = await db.execute("SELECT * FROM categories WHERE name = ?", (name,))
    row = await cursor.fetchone()

    if not row:
        return None

    return _row_to_category_response(dict(row))


async def get_all_categories(
    db: aiosqlite.Connection,
    category_type: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> CategoryListResponse:
    """Get all categories with optional filters."""
    query = "SELECT * FROM categories WHERE 1=1"
    params = []

    if category_type:
        query += " AND type = ?"
        params.append(category_type)

    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)

    query += " ORDER BY type, name"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()

    categories = [_row_to_category_response(dict(row)) for row in rows]

    return CategoryListResponse(categories=categories, total=len(categories))


async def update_category(
    db: aiosqlite.Connection, category_id: int, category: CategoryUpdate
) -> Optional[CategoryResponse]:
    """Update a category."""
    update_data = category.model_dump(exclude_unset=True)

    if not update_data:
        return await get_category(db, category_id)

    if "is_active" in update_data:
        update_data["is_active"] = 1 if update_data["is_active"] else 0

    set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
    values = list(update_data.values()) + [category_id]

    await db.execute(f"UPDATE categories SET {set_clause} WHERE id = ?", values)
    await db.commit()

    return await get_category(db, category_id)


async def delete_category(db: aiosqlite.Connection, category_id: int) -> bool:
    """
    Delete a category.
    Note: System categories cannot be deleted, only deactivated.
    """
    cursor = await db.execute(
        "SELECT is_system FROM categories WHERE id = ?", (category_id,)
    )
    row = await cursor.fetchone()

    if not row:
        return False

    if row["is_system"]:
        await db.execute(
            "UPDATE categories SET is_active = 0 WHERE id = ?", (category_id,)
        )
        await db.commit()
        return True

    cursor = await db.execute(
        "DELETE FROM categories WHERE id = ? AND is_system = 0", (category_id,)
    )
    await db.commit()

    return cursor.rowcount > 0


def _row_to_category_response(row: dict) -> CategoryResponse:
    """Convert a database row to a CategoryResponse."""
    created_at = row.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    return CategoryResponse(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        is_system=bool(row["is_system"]),
        is_active=bool(row["is_active"]),
        created_at=created_at or datetime.now(),
    )
