from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class BehavioralBaseline(SQLModel, table=True):
    """
    Stores the learned normal behavioral profile
    for an employee.

    Baselines are periodically recalculated from
    historical behavioral windows.
    """

    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    employee_id: int = Field(
        foreign_key="employee.id",
        unique=True,
        index=True
    )

    # ---------------------------------------------
    # Activity volume
    # ---------------------------------------------

    avg_events_per_window: float = 0.0
    std_events_per_window: float = 0.0

    avg_files_created: float = 0.0
    std_files_created: float = 0.0

    avg_files_modified: float = 0.0
    std_files_modified: float = 0.0

    avg_files_deleted: float = 0.0
    std_files_deleted: float = 0.0

    avg_files_moved: float = 0.0
    std_files_moved: float = 0.0

    # ---------------------------------------------
    # Sensitive activity
    # ---------------------------------------------

    avg_sensitive_events: float = 0.0
    std_sensitive_events: float = 0.0

    avg_sensitive_ratio: float = 0.0
    std_sensitive_ratio: float = 0.0

    # ---------------------------------------------
    # Data movement
    # ---------------------------------------------

    avg_data_volume: float = 0.0
    std_data_volume: float = 0.0

    # ---------------------------------------------
    # Behavioral diversity
    # ---------------------------------------------

    avg_unique_extensions: float = 0.0
    std_unique_extensions: float = 0.0

    avg_directory_breadth: float = 0.0
    std_directory_breadth: float = 0.0

    avg_activity_rate: float = 0.0
    std_activity_rate: float = 0.0

    # ---------------------------------------------
    # Temporal behavior
    # ---------------------------------------------

    after_hours_ratio: float = 0.0

    # ---------------------------------------------
    # Training metadata
    # ---------------------------------------------

    sample_count: int = 0

    last_trained_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )