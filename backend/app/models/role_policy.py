from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class RolePolicy(SQLModel, table=True):
    """
    Defines the normal behavioral and authorization boundaries
    associated with an employee role.

    Policies describe what a role is normally permitted to do.
    They do NOT disable behavioral monitoring.
    """

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    role: str = Field(
        index=True,
        unique=True,
    )

    description: str = ""

    # ---------------------------------------------------------
    # AUTHORIZED ACTIVITY
    # ---------------------------------------------------------
    allowed_activities: str = ""

    # ---------------------------------------------------------
    # SENSITIVE DATA
    # ---------------------------------------------------------
    sensitive_data_access_allowed: bool = False

    # ---------------------------------------------------------
    # VOLUME / BEHAVIORAL BOUNDARIES
    # ---------------------------------------------------------
    max_data_volume_per_window: int = 0

    max_sensitive_events_per_window: int = 0

    # ---------------------------------------------------------
    # TIME POLICY
    # ---------------------------------------------------------
    working_hours_start: str = "09:00"
    working_hours_end: str = "18:00"

    weekend_activity_allowed: bool = False

    # ---------------------------------------------------------
    # POLICY STATUS
    # ---------------------------------------------------------
    is_active: bool = True

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )