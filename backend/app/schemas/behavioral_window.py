from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BehavioralWindowCreate(BaseModel):

    window_start: datetime
    window_end: datetime

    # ---------------------------------------------------------
    # OBSERVED ACTIVITY
    # ---------------------------------------------------------
    observed_activity: str = ""

    # ---------------------------------------------------------
    # EVENT COUNTS
    # ---------------------------------------------------------
    total_events: int = Field(ge=0)

    files_created: int = Field(default=0, ge=0)
    files_modified: int = Field(default=0, ge=0)
    files_deleted: int = Field(default=0, ge=0)
    files_moved: int = Field(default=0, ge=0)

    # ---------------------------------------------------------
    # SENSITIVE DATA
    # ---------------------------------------------------------
    sensitive_events: int = Field(default=0, ge=0)
    sensitive_ratio: float = Field(default=0.0, ge=0.0, le=1.0)

    # ---------------------------------------------------------
    # VOLUME / DIVERSITY
    # ---------------------------------------------------------
    total_data_volume: int = Field(default=0, ge=0)
    unique_extensions: int = Field(default=0, ge=0)
    directory_breadth: int = Field(default=0, ge=0)

    # ---------------------------------------------------------
    # BEHAVIOR
    # ---------------------------------------------------------
    activity_rate: float = Field(default=0.0, ge=0.0)
    after_hours: bool = False

    session_id: Optional[str] = None

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------
    @field_validator("observed_activity")
    @classmethod
    def validate_observed_activity(cls, value: str) -> str:
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
                f"Invalid observed activity types: {sorted(invalid)}. "
                f"Allowed values: {sorted(allowed)}"
            )

        return ",".join(sorted(activities))

    @field_validator("sensitive_events")
    @classmethod
    def validate_sensitive_events(cls, value: int) -> int:
        if value < 0:
            raise ValueError("sensitive_events cannot be negative.")
        return value

    @field_validator("sensitive_ratio")
    @classmethod
    def validate_sensitive_ratio(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("sensitive_ratio must be between 0 and 1.")
        return value


class BehavioralWindowRead(BaseModel):
    id: int
    device_id: int

    window_start: datetime
    window_end: datetime

    observed_activity: str

    total_events: int

    files_created: int
    files_modified: int
    files_deleted: int
    files_moved: int

    sensitive_events: int
    sensitive_ratio: float

    total_data_volume: int
    unique_extensions: int
    directory_breadth: int

    activity_rate: float
    after_hours: bool

    session_id: Optional[str]
    created_at: datetime