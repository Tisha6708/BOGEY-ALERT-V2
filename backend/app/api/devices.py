import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.device import Device
from app.models.employee import Employee
from app.schemas.device import (
    DeviceCreate,
    DeviceRegistrationResponse,
    DeviceRead,
)


router = APIRouter(
    prefix="/devices",
    tags=["Devices"]
)


def hash_credential(credential: str) -> str:
    return hashlib.sha256(
        credential.encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------
# REGISTER DEVICE
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=DeviceRegistrationResponse,
    status_code=201
)
def register_device(
    device_data: DeviceCreate,
    session: Session = Depends(get_session)
):
    # 1. Verify employee exists
    employee = session.get(
        Employee,
        device_data.employee_id
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    # 2. Don't allow inactive employees
    if not employee.is_active:
        raise HTTPException(
            status_code=403,
            detail="Employee is inactive"
        )

    # 3. Check duplicate device code
    existing_device = session.exec(
        select(Device).where(
            Device.device_code == device_data.device_code
        )
    ).first()

    if existing_device:
        raise HTTPException(
            status_code=409,
            detail="Device code already exists"
        )

    # 4. Generate secure credential
    raw_credential = secrets.token_urlsafe(32)

    # 5. Store only credential hash
    credential_hash = hash_credential(
        raw_credential
    )

    # 6. Create device
    device = Device(
        device_code=device_data.device_code,
        employee_id=device_data.employee_id,
        operating_system=device_data.operating_system,
        agent_version=device_data.agent_version,
        credential_hash=credential_hash,
        last_seen=datetime.now(timezone.utc)
    )

    session.add(device)
    session.commit()
    session.refresh(device)

    # 7. Raw credential returned ONLY during registration
    return {
        **device.model_dump(),
        "device_credential": raw_credential
    }


# ---------------------------------------------------------
# LIST DEVICES
# ---------------------------------------------------------
@router.get(
    "/",
    response_model=list[DeviceRead]
)
def get_devices(
    session: Session = Depends(get_session)
):
    devices = session.exec(
        select(Device).order_by(Device.id)
    ).all()

    return list(devices)


# ---------------------------------------------------------
# GET SINGLE DEVICE
# ---------------------------------------------------------
@router.get(
    "/{device_id}",
    response_model=DeviceRead
)
def get_device(
    device_id: int,
    session: Session = Depends(get_session)
):
    device = session.get(
        Device,
        device_id
    )

    if not device:
        raise HTTPException(
            status_code=404,
            detail="Device not found"
        )

    return device