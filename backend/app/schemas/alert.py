from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlertRead(BaseModel):
    id: int
    employee_id: int
    device_id: int
    behavioral_window_id: int

    risk_score: int
    risk_level: str
    status: str

    reasons: list[str]

    created_at: datetime
    reviewed_at: Optional[datetime] = None

    analyst_decision: Optional[str] = None
    analyst_notes: Optional[str] = None


class AlertReviewRequest(BaseModel):
    status: str
    analyst_notes: Optional[str] = None