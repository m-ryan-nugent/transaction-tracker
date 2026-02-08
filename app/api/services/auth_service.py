"""Authentication service"""

from typing import Optional
from datetime import datetime, timedelta, timezone

import bcrypt
import aiosqlite
from jose import JWTError, jwt

from app.config import (
    SECRET_KEY,
    TOKEN_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.api.schemas.auth import UserCreate, UserResponse, TokenData


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=TOKEN_ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
        
        return TokenData(username=username)
    except JWTError:
        return None


async def create_user(db: aiosqlite.Connection, user: UserCreate) -> UserResponse:
    """Create a new user."""
    hashed_password = hash_password(user.password)
    
    cursor = await db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (user.username, hashed_password)
    )
    await db.commit()
    
    return await get_user_by_id(db, cursor.lastrowid)


async def get_user_by_username(db: aiosqlite.Connection, username: str) -> Optional[dict]:
    """Get a user by username (includes password hash for auth)."""
    cursor = await db.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    )
    row = await cursor.fetchone()
    
    if row:
        return dict(row)
    return None


async def get_user_by_id(db: aiosqlite.Connection, user_id: int) -> Optional[UserResponse]:
    """Get a user by ID (excludes password hash)."""
    cursor = await db.execute(
        "SELECT id, username, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    row = await cursor.fetchone()
    
    if row:
        row_dict = dict(row)
        created_at = row_dict.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return UserResponse(
            id=row_dict["id"],
            username=row_dict["username"],
            created_at=created_at or datetime.now(),
        )
    return None


async def authenticate_user(db: aiosqlite.Connection, username: str, password: str) -> Optional[dict]:
    """Authenticate a user and return user data if valid."""
    user = await get_user_by_username(db, username)
    
    if not user:
        return None
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    return user


async def user_exists(db: aiosqlite.Connection) -> bool:
    """Check if any user exists (for initial setup)."""
    cursor = await db.execute("SELECT COUNT(*) as count FROM users")
    row = await cursor.fetchone()
    
    return row["count"] > 0