from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import verify_device_credential
from app.db.session import get_session
from app.models.device import Device
from app.models.employee import Employee
from app.schemas.auth import (
    AgentLoginRequest,
    AgentLoginResponse
)


router = APIRouter(
    prefix="/agent",
    tags=["Agent Authentication"]
)


@router.post(
    "/login",
    response_model=AgentLoginResponse
)
def agent_login(
    login_data: AgentLoginRequest,
    session: Session = Depends(get_session)
):
    device = session.exec(
        select(Device).where(
            Device.device_code == login_data.device_code
        )
    ).first()

    if not device:
        raise HTTPException(
            status_code=401,
            detail="Invalid device credentials"
        )

    if not device.is_active:
        raise HTTPException(
            status_code=403,
            detail="Device is inactive"
        )

    if not verify_device_credential(
        login_data.device_credential,
        device.credential_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid device credentials"
        )

    employee = session.get(
        Employee,
        device.employee_id
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Associated employee not found"
        )

    if not employee.is_active:
        raise HTTPException(
            status_code=403,
            detail="Associated employee is inactive"
        )

    device.last_seen = datetime.now(timezone.utc)

    session.add(device)
    session.commit()

    return AgentLoginResponse(
        access_token=login_data.device_credential,
        device_id=device.id,
        employee_id=employee.id
    )