"""
Authentication endpoints.

Handles user registration, login, token refresh, logout, and profile.
"""

from datetime import datetime, UTC
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import Field

from maverick_schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserProfile,
)
from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.responses import APIResponse, ResponseMeta
from maverick_services import UserService, AuthenticationError, ConflictError, NotFoundError
from maverick_api.dependencies import get_db, get_current_user, get_request_id, get_redis
from maverick_api.auth.jwt import JWTAuthStrategy
from maverick_api.auth.cookie import CookieAuthStrategy
from maverick_api.config import get_settings
from maverick_schemas.auth import AuthenticatedUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service with database session."""
    return UserService(db=db)


async def get_jwt_strategy(request: Request) -> JWTAuthStrategy:
    """Get JWT strategy from app state."""
    settings = get_settings()
    redis = await get_redis()
    return JWTAuthStrategy(
        secret_key=settings.jwt_secret,
        redis=redis,
        access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
        refresh_token_expire_days=settings.jwt_refresh_token_expire_days,
    )


async def get_cookie_strategy(request: Request) -> CookieAuthStrategy:
    """Get cookie strategy from app state."""
    settings = get_settings()
    redis = await get_redis()
    return CookieAuthStrategy(redis=redis, secure=settings.is_production)


@router.post("/register", response_model=APIResponse[dict])
async def register(
    data: RegisterRequest,
    request_id: str = Depends(get_request_id),
    user_service: UserService = Depends(get_user_service),
):
    """
    Register a new user account.
    
    Creates a new user with email and password. Returns user info
    (but not tokens - user must login separately).
    """
    try:
        result = await user_service.register(
            email=data.email,
            password=data.password,
        )
        
        return APIResponse(
            data=result,
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login(
    data: LoginRequest,
    response: Response,
    request_id: str = Depends(get_request_id),
    user_service: UserService = Depends(get_user_service),
    jwt_strategy: JWTAuthStrategy = Depends(get_jwt_strategy),
    cookie_strategy: CookieAuthStrategy = Depends(get_cookie_strategy),
):
    """
    Login with email and password.
    
    Returns JWT tokens for API access. Also sets session cookie
    for web clients.
    """
    try:
        # Authenticate user
        user = await user_service.authenticate(
            email=data.email,
            password=data.password,
        )
        
        # Generate JWT tokens (returns TokenResponse object)
        token_response = jwt_strategy.create_tokens(
            user_id=user.user_id,
            tier=user.tier,
        )
        
        # Also set session cookie for web clients
        await cookie_strategy.create_session(
            response=response,
            user_id=user.user_id,
            tier=str(user.tier),
        )
        
        return APIResponse(
            data=token_response,
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_tokens(
    data: RefreshTokenRequest,
    request_id: str = Depends(get_request_id),
    jwt_strategy: JWTAuthStrategy = Depends(get_jwt_strategy),
):
    """
    Refresh access token using refresh token.
    
    Implements refresh token rotation - each refresh token can only
    be used once. If a refresh token is reused, all tokens for the
    user are invalidated (potential token theft).
    """
    try:
        # refresh_tokens returns TokenResponse object directly
        token_response = await jwt_strategy.refresh_tokens(data.refresh_token)
        
        return APIResponse(
            data=token_response,
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    cookie_strategy: CookieAuthStrategy = Depends(get_cookie_strategy),
):
    """
    Logout the current user.
    
    Clears session cookie and invalidates current session.
    Note: JWT tokens cannot be invalidated directly - they expire naturally.
    """
    try:
        # Clear session cookie
        session_id = request.cookies.get(cookie_strategy.SESSION_COOKIE_NAME)
        if session_id:
            await cookie_strategy.invalidate_session(session_id)
        
        # Clear cookies
        response.delete_cookie(cookie_strategy.SESSION_COOKIE_NAME)
        response.delete_cookie(cookie_strategy.CSRF_COOKIE_NAME)
        
        return APIResponse(
            data={"message": "Logged out successfully"},
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        # Even if there's an error, clear cookies
        response.delete_cookie(cookie_strategy.SESSION_COOKIE_NAME)
        response.delete_cookie(cookie_strategy.CSRF_COOKIE_NAME)
        return APIResponse(
            data={"message": "Logged out"},
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )


@router.get("/me", response_model=APIResponse[UserProfile])
async def get_current_user_profile(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get the current authenticated user's profile.
    """
    try:
        profile = await user_service.get_by_id(user.user_id)
        
        user_profile = UserProfile(
            user_id=profile["user_id"],
            email=profile["email"],
            tier=profile["tier"],
            email_verified=profile["email_verified"],
            created_at=profile["created_at"],
            last_login_at=profile["last_login_at"],
        )
        
        return APIResponse(
            data=user_profile,
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get profile failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")


class ChangePasswordRequest(MaverickBaseModel):
    """Request body for password change."""
    
    current_password: str = Field(min_length=1, description="Current password")
    new_password: str = Field(min_length=8, max_length=128, description="New password")


@router.put("/password")
async def change_password(
    data: ChangePasswordRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Change the current user's password.
    
    Requires the current password for verification.
    """
    try:
        await user_service.update_password(
            user_id=user.user_id,
            current_password=data.current_password,
            new_password=data.new_password,
        )
        
        return APIResponse(
            data={"message": "Password updated successfully"},
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to change password")

