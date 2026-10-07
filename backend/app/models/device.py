from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Device(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True
    )

    device_code: str = Field(
        index=True,
        unique=True
    )

    employee_id: int = Field(
        foreign_key="employee.id",
        index=True
    )

    operating_system: str

    agent_version: str = "1.0.0"

    # Store only the hash of the device credential.
    # The actual credential is shown to the admin once
    # during registration and is never stored directly.
    credential_hash: str

    is_active: bool = Field(default=True)

    last_seen: Optional[datetime] = None

    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )