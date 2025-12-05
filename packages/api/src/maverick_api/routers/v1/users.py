"""
User profile endpoints.

Handles user profile management, onboarding, and settings.
"""

from datetime import datetime, UTC
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import Field

from maverick_schemas.auth import UserProfile, MessageResponse
from maverick_schemas.base import MaverickBaseModel
from maverick_schemas.responses import APIResponse, ResponseMeta
from maverick_services import UserService, NotFoundError
from maverick_api.dependencies import get_db, get_current_user, get_request_id
from maverick_schemas.auth import AuthenticatedUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service with database session."""
    return UserService(db=db)


class UpdateProfileRequest(MaverickBaseModel):
    """Request to update user profile."""
    
    name: str | None = Field(default=None, max_length=100, description="Display name")


class OnboardingStatus(MaverickBaseModel):
    """Onboarding status response."""
    
    completed: bool = Field(description="Whether onboarding is completed")
    steps_completed: list[str] = Field(default_factory=list, description="Completed steps")


@router.get("/me", response_model=APIResponse[UserProfile])
async def get_my_profile(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get the current user's profile.
    
    Alias for /auth/me for consistency.
    """
    try:
        profile = await user_service.get_by_id(user.user_id)
        
        return APIResponse(
            data=UserProfile(
                user_id=profile["user_id"],
                email=profile["email"],
                name=profile.get("name"),
                tier=profile["tier"],
                email_verified=profile["email_verified"],
                onboarding_completed=profile.get("onboarding_completed", False),
                is_demo_user=profile.get("is_demo_user", False),
                created_at=profile["created_at"],
                last_login_at=profile["last_login_at"],
            ),
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


@router.patch("/me", response_model=APIResponse[UserProfile])
async def update_my_profile(
    data: UpdateProfileRequest,
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Update the current user's profile.
    """
    try:
        profile = await user_service.update_profile(
            user_id=user.user_id,
            name=data.name,
        )
        
        return APIResponse(
            data=UserProfile(
                user_id=profile["user_id"],
                email=profile["email"],
                name=profile.get("name"),
                tier=profile["tier"],
                email_verified=profile["email_verified"],
                onboarding_completed=profile.get("onboarding_completed", False),
                is_demo_user=profile.get("is_demo_user", False),
                created_at=profile["created_at"],
                last_login_at=profile["last_login_at"],
            ),
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Update profile failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.get("/me/onboarding", response_model=APIResponse[OnboardingStatus])
async def get_onboarding_status(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get the current user's onboarding status.
    """
    try:
        profile = await user_service.get_by_id(user.user_id)
        
        return APIResponse(
            data=OnboardingStatus(
                completed=profile.get("onboarding_completed", False),
                steps_completed=[],  # Can be expanded for multi-step onboarding
            ),
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Get onboarding status failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get onboarding status")


@router.post("/me/onboarding/complete", response_model=APIResponse[MessageResponse])
async def complete_onboarding(
    request_id: str = Depends(get_request_id),
    user: AuthenticatedUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """
    Mark the current user's onboarding as complete.
    """
    try:
        await user_service.complete_onboarding(user_id=user.user_id)
        
        return APIResponse(
            data=MessageResponse(message="Onboarding completed successfully"),
            meta=ResponseMeta(
                request_id=request_id,
                timestamp=datetime.now(UTC),
            ),
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Complete onboarding failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete onboarding")

