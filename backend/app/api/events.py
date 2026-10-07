from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.core.security import get_authenticated_device
from app.db.session import get_session
from app.models.activity_event import ActivityEvent
from app.models.device import Device
from app.schemas.activity_event import (
    ActivityEventCreate,
    ActivityEventRead,
)

router = APIRouter(
    prefix="/events",
    tags=["Activity Events"]
)


@router.post(
    "/",
    response_model=ActivityEventRead,
    status_code=status.HTTP_201_CREATED
)
def create_activity_event(
    event_data: ActivityEventCreate,
    device: Device = Depends(get_authenticated_device),
    session: Session = Depends(get_session)
):
    event = ActivityEvent(
        device_id=device.id,
        timestamp=(
            event_data.timestamp
            if event_data.timestamp
            else datetime.now(timezone.utc)
        ),
        event_type=event_data.event_type,
        file_extension=event_data.file_extension,
        file_size=max(event_data.file_size, 0),
        is_sensitive=event_data.is_sensitive,
        directory_type=event_data.directory_type,
        session_id=event_data.session_id
    )

    session.add(event)

    # Update device heartbeat whenever
    # the agent sends activity.
    device.last_seen = datetime.now(timezone.utc)
    session.add(device)

    session.commit()
    session.refresh(event)

    return event