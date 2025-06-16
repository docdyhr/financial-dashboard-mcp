"""User settings API endpoints for managing user preferences."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models import get_db
from backend.models.user_settings import UserSettings
from backend.schemas.base import BaseResponse
from backend.schemas.user_settings import (
    UserSettingsBulkUpdate,
    UserSettingsCreate,
    UserSettingsPreferences,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from backend.services.user_settings import UserSettingsService

router = APIRouter()
user_settings_service = UserSettingsService()


@router.get("/{user_id}", response_model=BaseResponse[UserSettingsResponse])
async def get_user_settings(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[UserSettingsResponse]:
    """Get user settings for a specific user."""
    try:
        settings = user_settings_service.get_user_settings(db, user_id)

        if not settings:
            # Create default settings if none exist
            default_settings = UserSettingsCreate(
                user_id=user_id, **UserSettings.get_default_settings()
            )
            settings = user_settings_service.create_user_settings(db, default_settings)

        return BaseResponse(
            success=True,
            message="User settings retrieved successfully",
            data=UserSettingsResponse(**settings.to_dict()),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/", response_model=BaseResponse[UserSettingsResponse])
async def create_user_settings(
    settings_create: UserSettingsCreate, db: Session = Depends(get_db)
) -> BaseResponse[UserSettingsResponse]:
    """Create new user settings."""
    try:
        # Check if settings already exist for this user
        existing_settings = user_settings_service.get_user_settings(
            db, settings_create.user_id
        )
        if existing_settings:
            raise HTTPException(
                status_code=400,
                detail=f"Settings already exist for user {settings_create.user_id}",
            )

        settings = user_settings_service.create_user_settings(db, settings_create)
        return BaseResponse(
            success=True,
            message="User settings created successfully",
            data=UserSettingsResponse(**settings.to_dict()),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{user_id}", response_model=BaseResponse[UserSettingsResponse])
async def update_user_settings(
    user_id: int, settings_update: UserSettingsUpdate, db: Session = Depends(get_db)
) -> BaseResponse[UserSettingsResponse]:
    """Update user settings."""
    try:
        settings = user_settings_service.update_user_settings(
            db, user_id, settings_update
        )
        if not settings:
            raise HTTPException(status_code=404, detail="User settings not found")

        return BaseResponse(
            success=True,
            message="User settings updated successfully",
            data=UserSettingsResponse(**settings.to_dict()),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/{user_id}/bulk", response_model=BaseResponse[UserSettingsResponse])
async def bulk_update_user_settings(
    user_id: int, bulk_update: UserSettingsBulkUpdate, db: Session = Depends(get_db)
) -> BaseResponse[UserSettingsResponse]:
    """Bulk update multiple user settings at once."""
    try:
        settings = user_settings_service.bulk_update_user_settings(
            db, user_id, bulk_update.settings
        )
        if not settings:
            raise HTTPException(status_code=404, detail="User settings not found")

        return BaseResponse(
            success=True,
            message="User settings updated successfully",
            data=UserSettingsResponse(**settings.to_dict()),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{user_id}", response_model=BaseResponse[Any])
async def delete_user_settings(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[Any]:
    """Delete user settings (reset to defaults)."""
    try:
        success = user_settings_service.delete_user_settings(db, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User settings not found")

        return BaseResponse(
            success=True,
            message="User settings deleted successfully",
            data=None,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{user_id}/reset", response_model=BaseResponse[UserSettingsResponse])
async def reset_user_settings(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[UserSettingsResponse]:
    """Reset user settings to defaults."""
    try:
        settings = user_settings_service.reset_to_defaults(db, user_id)
        return BaseResponse(
            success=True,
            message="User settings reset to defaults",
            data=UserSettingsResponse(**settings.to_dict()),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/{user_id}/preferences", response_model=BaseResponse[UserSettingsPreferences]
)
async def get_user_preferences(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[UserSettingsPreferences]:
    """Get simplified user preferences for frontend."""
    try:
        settings = user_settings_service.get_user_settings(db, user_id)

        if not settings:
            # Create default settings if none exist
            default_settings = UserSettingsCreate(
                user_id=user_id, **UserSettings.get_default_settings()
            )
            settings = user_settings_service.create_user_settings(db, default_settings)

        # Convert to simplified preferences format
        preferences = UserSettingsPreferences(
            theme=settings.theme,
            currency=settings.preferred_currency,
            date_format=settings.date_format,
            provider=settings.preferred_data_provider,
            frequency=settings.price_update_frequency,
            email_enabled=settings.email_notifications_enabled,
            email=settings.notification_email,
            price_alerts=settings.price_alerts_enabled,
            performance_alerts=settings.performance_alerts_enabled,
            news_alerts=settings.news_alerts_enabled,
        )

        return BaseResponse(
            success=True,
            message="User preferences retrieved successfully",
            data=preferences,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put(
    "/{user_id}/preferences", response_model=BaseResponse[UserSettingsPreferences]
)
async def update_user_preferences(
    user_id: int, preferences: UserSettingsPreferences, db: Session = Depends(get_db)
) -> BaseResponse[UserSettingsPreferences]:
    """Update simplified user preferences from frontend."""
    try:
        # Convert preferences to settings update format
        settings_update = UserSettingsUpdate(
            theme=preferences.theme,
            preferred_currency=preferences.currency,
            date_format=preferences.date_format,
            preferred_data_provider=preferences.provider,
            price_update_frequency=preferences.frequency,
            email_notifications_enabled=preferences.email_enabled,
            notification_email=preferences.email,
            price_alerts_enabled=preferences.price_alerts,
            performance_alerts_enabled=preferences.performance_alerts,
            news_alerts_enabled=preferences.news_alerts,
        )

        settings = user_settings_service.update_user_settings(
            db, user_id, settings_update
        )
        if not settings:
            raise HTTPException(status_code=404, detail="User settings not found")

        # Return updated preferences
        updated_preferences = UserSettingsPreferences(
            theme=settings.theme,
            currency=settings.preferred_currency,
            date_format=settings.date_format,
            provider=settings.preferred_data_provider,
            frequency=settings.price_update_frequency,
            email_enabled=settings.email_notifications_enabled,
            email=settings.notification_email,
            price_alerts=settings.price_alerts_enabled,
            performance_alerts=settings.performance_alerts_enabled,
            news_alerts=settings.news_alerts_enabled,
        )

        return BaseResponse(
            success=True,
            message="User preferences updated successfully",
            data=updated_preferences,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{user_id}/export", response_model=BaseResponse[dict[str, Any]])
async def export_user_settings(
    user_id: int, db: Session = Depends(get_db)
) -> BaseResponse[dict[str, Any]]:
    """Export user settings as JSON for backup/transfer."""
    try:
        settings = user_settings_service.get_user_settings(db, user_id)
        if not settings:
            raise HTTPException(status_code=404, detail="User settings not found")

        export_data = {
            "user_id": user_id,
            "settings": settings.to_dict(),
            "export_timestamp": (
                settings.updated_at.isoformat() if settings.updated_at else None
            ),
        }

        return BaseResponse(
            success=True,
            message="User settings exported successfully",
            data=export_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{user_id}/import", response_model=BaseResponse[UserSettingsResponse])
async def import_user_settings(
    user_id: int, import_data: dict[str, Any], db: Session = Depends(get_db)
) -> BaseResponse[UserSettingsResponse]:
    """Import user settings from JSON backup."""
    try:
        if "settings" not in import_data:
            raise HTTPException(status_code=400, detail="Invalid import data format")

        settings_data = import_data["settings"]

        # Remove fields that shouldn't be imported
        settings_data.pop("id", None)
        settings_data.pop("created_at", None)
        settings_data.pop("updated_at", None)
        settings_data["user_id"] = user_id  # Ensure correct user_id

        # Create or update settings
        existing_settings = user_settings_service.get_user_settings(db, user_id)

        if existing_settings:
            # Update existing settings
            settings_update = UserSettingsUpdate(
                **{
                    k: v
                    for k, v in settings_data.items()
                    if k not in ["id", "user_id", "created_at", "updated_at"]
                }
            )
            settings = user_settings_service.update_user_settings(
                db, user_id, settings_update
            )
        else:
            # Create new settings
            settings_create = UserSettingsCreate(**settings_data)
            settings = user_settings_service.create_user_settings(db, settings_create)

        if settings:
            return BaseResponse(
                success=True,
                message="User settings imported successfully",
                data=UserSettingsResponse(**settings.to_dict()),
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to import settings")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
