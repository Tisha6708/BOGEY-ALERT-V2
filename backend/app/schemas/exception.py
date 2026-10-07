from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExceptionCreate(BaseModel):
    employee_id: int
    reason: str
    authorized_by: str
    start_time: datetime
    end_time: datetime
    allowed_activity: str


class ExceptionRead(BaseModel):
    id: int
    employee_id: int
    reason: str
    authorized_by: str
    start_time: datetime
    end_time: datetime
    allowed_activity: str
    status: str
    created_at: datetime


class ExceptionStatusUpdate(BaseModel):
    status: str