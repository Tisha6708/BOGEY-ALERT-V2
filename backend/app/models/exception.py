from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ExceptionAuthorization(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    employee_id: int = Field(
        foreign_key="employee.id",
        index=True,
    )

    reason: str

    authorized_by: str

    start_time: datetime = Field(
        index=True,
    )

    end_time: datetime = Field(
        index=True,
    )

    allowed_activity: str

    status: str = Field(
        default="ACTIVE",
        index=True,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )