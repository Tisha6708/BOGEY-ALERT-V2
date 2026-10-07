from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    employee_code: str = Field(
        index=True,
        unique=True
    )

    role: str = Field(index=True)

    department: str = Field(index=True)

    manager_id: Optional[int] = Field(
        default=None,
        foreign_key="employee.id"
    )

    is_active: bool = Field(default=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )