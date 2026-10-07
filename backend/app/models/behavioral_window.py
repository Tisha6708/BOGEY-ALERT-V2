from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class BehavioralWindow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    device_id: int = Field(
        foreign_key="device.id",
        index=True
    )

    window_start: datetime = Field(index=True)
    window_end: datetime = Field(index=True)

    # ---------------------------------------------------------
    # OBSERVED ACTIVITY
    # ---------------------------------------------------------
    # Comma-separated categories of activity actually observed
    # by the endpoint agent during this window.
    #
    # Examples:
    #   "create,modify"
    #   "modify,delete"
    #   "move"
    #
    # This describes observed filesystem activity.
    # It does NOT claim that a file was read or transferred
    # unless the endpoint actually observes such an event.
    observed_activity: str = Field(
        default="",
        index=True
    )

    # ---------------------------------------------------------
    # EVENT COUNTS
    # ---------------------------------------------------------
    total_events: int = 0

    files_created: int = 0
    files_modified: int = 0
    files_deleted: int = 0
    files_moved: int = 0

    # ---------------------------------------------------------
    # SENSITIVE DATA
    # ---------------------------------------------------------
    sensitive_events: int = 0
    sensitive_ratio: float = 0.0

    # ---------------------------------------------------------
    # VOLUME / DIVERSITY
    # ---------------------------------------------------------
    total_data_volume: int = 0
    unique_extensions: int = 0
    directory_breadth: int = 0

    # ---------------------------------------------------------
    # BEHAVIOR
    # ---------------------------------------------------------
    activity_rate: float = 0.0
    after_hours: bool = False

    session_id: Optional[str] = Field(
        default=None,
        index=True
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )