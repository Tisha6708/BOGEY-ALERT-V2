from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DeviceCreate(BaseModel):
    device_code: str
    employee_id: int
    operating_system: str
    agent_version: str = "1.0.0"


class DeviceRead(BaseModel):
    id: int
    device_code: str
    employee_id: int
    operating_system: str
    agent_version: str
    is_active: bool
    last_seen: Optional[datetime] = None


class DeviceRegistrationResponse(DeviceRead):
    """
    Returned only once during device registration.

    The raw credential is intentionally not stored
    in the database.
    """

    device_credential: str

    model_config = ConfigDict(
        from_attributes=True
    )