"""Authentication schemas"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a new user (initial setup)."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token data."""
    username: str | None = None


class UserResponse(BaseModel):
    """Schema for user response (no password)."""
    id: int
    username: str
    created_at: datetime
    
    model_config = {"from_attributes": True}
