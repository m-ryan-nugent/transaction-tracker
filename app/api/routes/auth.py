"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_db, get_current_user
from app.api.schemas.auth import UserCreate, UserResponse, Token
from app.api.services import auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/setup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def setup_user(user: UserCreate, db=Depends(get_db)):
    """Initial user setup. Only works if no user exists."""
    if await auth_service.user_exists(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists. Use /auth/login instead.",
        )
    
    return await auth_service.create_user(db, user)


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db=Depends(get_db),
):
    """Login with username and password."""
    user = await auth_service.authenticate_user(
        db, form_data.username, form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth_service.create_access_token(data={"sub": user["username"]})

    # Set token as HTTP-only cookie for web clients
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
    )

    return Token(access_token=access_token)


@router.post("/logout")
async def logout(response: Response):
    """Logout by clearing the auth cookie."""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Get current user information."""
    user = await auth_service.get_user_by_username(db, current_user["username"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return UserResponse(
        id=user["id"],
        username=user["username"],
        created_at=user["created_at"],
    )


@router.get("/status")
async def auth_status(db=Depends(get_db)):
    """Check authentication status."""
    user_exists = await auth_service.user_exists(db)

    return {
        "setup_required": not user_exists,
        "message": "Please create a user account" if not user_exists else "Ready"
    }
