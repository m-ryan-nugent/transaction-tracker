"""API dependencies"""

from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from app.database import get_db as _get_db
from app.api.services.auth_service import decode_access_token, get_user_by_username


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_db():
    """
    Database dependency.
    """
    db = await _get_db()
    try:
        yield db
    finally:
        await db.close()


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    """
    Get the current authenticated user.
    Checks both Authorization header and HTTP-only cookie.
    Raises HTTPException if not authenticated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        cookie_token = request.cookies.get("access_token")
        if cookie_token and cookie_token.startswith("Bearer "):
            token = cookie_token[7:]  # Remove "Bearer " prefix

    if not token:
        raise credentials_exception

    token_data = decode_access_token(token)

    if token_data is None or token_data.username is None:
        raise credentials_exception

    user = await get_user_by_username(db, token_data.username)

    if user is None:
        raise credentials_exception

    return user


async def get_optional_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db=Depends(get_db),
):
    """
    Get the current user if authenticated, None otherwise.
    """
    try:
        return await get_current_user(request, token, db)
    except HTTPException:
        return None
