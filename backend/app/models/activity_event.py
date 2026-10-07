from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ActivityEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Device that generated the event.
    # The employee is derived through the device relationship.
    device_id: int = Field(
        foreign_key="device.id",
        index=True
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Examples:
    # create, modify, delete, move, copy
    event_type: str = Field(index=True)

    # We intentionally do NOT store the complete file path.
    # Only the extension is needed for behavioral analysis.
    file_extension: Optional[str] = Field(
        default=None,
        index=True
    )

    # Size of the affected file in bytes.
    file_size: int = 0

    # Whether the local agent classified this file
    # as potentially sensitive.
    is_sensitive: bool = False

    # Examples:
    # desktop, downloads, documents, company_workspace
    directory_type: str = Field(index=True)

    # Optional identifier used to correlate multiple
    # events belonging to the same local session/batch.
    session_id: Optional[str] = Field(
        default=None,
        index=True
    )