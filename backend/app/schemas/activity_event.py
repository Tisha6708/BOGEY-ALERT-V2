from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ActivityEventCreate(BaseModel):
    timestamp: Optional[datetime] = None

    event_type: str
    file_extension: Optional[str] = None
    file_size: int = 0
    is_sensitive: bool = False
    directory_type: str
    session_id: Optional[str] = None


class ActivityEventRead(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    event_type: str
    file_extension: Optional[str]
    file_size: int
    is_sensitive: bool
    directory_type: str
    session_id: Optional[str]