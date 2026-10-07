from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RolePolicyCreate(BaseModel):
    role: str = Field(min_length=1)
    description: str = ""

    allowed_activities: str = ""

    sensitive_data_access_allowed: bool = False

    max_data_volume_per_window: int = Field(
        default=0,
        ge=0,
    )

    max_sensitive_events_per_window: int = Field(
        default=0,
        ge=0,
    )

    working_hours_start: str = "09:00"
    working_hours_end: str = "18:00"

    weekend_activity_allowed: bool = False

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Role cannot be empty.")

        return value

    @field_validator("allowed_activities")
    @classmethod
    def validate_allowed_activities(cls, value: str) -> str:
        if not value:
            return ""

        allowed = {
            "create",
            "modify",
            "delete",
            "move",
        }

        activities = {
            activity.strip().lower()
            for activity in value.split(",")
            if activity.strip()
        }

        invalid = activities - allowed

        if invalid:
            raise ValueError(
                f"Invalid activity types: {sorted(invalid)}. "
                f"Allowed values: {sorted(allowed)}"
            )

        return ",".join(sorted(activities))

    @field_validator(
        "working_hours_start",
        "working_hours_end",
    )
    @classmethod
    def validate_working_hours(cls, value: str) -> str:
        try:
            hour, minute = value.split(":")

            hour = int(hour)
            minute = int(minute)

            if not (0 <= hour <= 23):
                raise ValueError

            if not (0 <= minute <= 59):
                raise ValueError

        except (ValueError, AttributeError):
            raise ValueError(
                "Working hours must use HH:MM format."
            )

        return f"{hour:02d}:{minute:02d}"


class RolePolicyUpdate(BaseModel):
    description: Optional[str] = None

    allowed_activities: Optional[str] = None

    sensitive_data_access_allowed: Optional[bool] = None

    max_data_volume_per_window: Optional[int] = Field(
        default=None,
        ge=0,
    )

    max_sensitive_events_per_window: Optional[int] = Field(
        default=None,
        ge=0,
    )

    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None

    weekend_activity_allowed: Optional[bool] = None

    is_active: Optional[bool] = None

    @field_validator("allowed_activities")
    @classmethod
    def validate_allowed_activities(cls, value):
        if value is None:
            return None

        allowed = {
            "create",
            "modify",
            "delete",
            "move",
        }

        activities = {
            activity.strip().lower()
            for activity in value.split(",")
            if activity.strip()
        }

        invalid = activities - allowed

        if invalid:
            raise ValueError(
                f"Invalid activity types: {sorted(invalid)}. "
                f"Allowed values: {sorted(allowed)}"
            )

        return ",".join(sorted(activities))

    @field_validator(
        "working_hours_start",
        "working_hours_end",
    )
    @classmethod
    def validate_working_hours(cls, value):
        if value is None:
            return None

        try:
            hour, minute = value.split(":")

            hour = int(hour)
            minute = int(minute)

            if not (0 <= hour <= 23):
                raise ValueError

            if not (0 <= minute <= 59):
                raise ValueError

        except (ValueError, AttributeError):
            raise ValueError(
                "Working hours must use HH:MM format."
            )

        return f"{hour:02d}:{minute:02d}"


class RolePolicyRead(BaseModel):
    id: int

    role: str

    description: str

    allowed_activities: str

    sensitive_data_access_allowed: bool

    max_data_volume_per_window: int

    max_sensitive_events_per_window: int

    working_hours_start: str

    working_hours_end: str

    weekend_activity_allowed: bool

    is_active: bool

    created_at: datetime

    updated_at: datetime