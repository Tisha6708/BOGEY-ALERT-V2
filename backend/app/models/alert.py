from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    employee_id: int = Field(
        foreign_key="employee.id",
        index=True,
    )

    device_id: int = Field(
        foreign_key="device.id",
        index=True,
    )

    behavioral_window_id: int = Field(
        foreign_key="behavioralwindow.id",
        index=True,
    )

    risk_score: int
    risk_level: str = Field(index=True)

    status: str = Field(
        default="PENDING",
        index=True,
    )

    reasons_json: str

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )

    reviewed_at: Optional[datetime] = None

    analyst_decision: Optional[str] = None

    analyst_notes: Optional[str] = None