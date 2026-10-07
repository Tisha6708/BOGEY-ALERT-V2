from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.security import get_authenticated_device
from app.db.session import get_session
from app.models.behavioral_window import BehavioralWindow
from app.models.device import Device
from app.services.window_processor import process_behavioral_window


router = APIRouter(
    prefix="/detection",
    tags=["Behavioral Detection"],
)


@router.post("/windows/{window_id}")
def analyze_behavioral_window(
    window_id: int,
    device: Device = Depends(get_authenticated_device),
    session: Session = Depends(get_session),
):
    # ---------------------------------------------------------
    # 1. FIND BEHAVIORAL WINDOW
    # ---------------------------------------------------------
    window = session.get(
        BehavioralWindow,
        window_id,
    )

    if not window:
        raise HTTPException(
            status_code=404,
            detail="Behavioral window not found.",
        )

    # ---------------------------------------------------------
    # 2. VERIFY DEVICE OWNERSHIP
    # ---------------------------------------------------------
    if window.device_id != device.id:
        raise HTTPException(
            status_code=403,
            detail=(
                "You are not authorized to analyze "
                "this behavioral window."
            ),
        )

    # ---------------------------------------------------------
    # 3. PROCESS WINDOW
    # ---------------------------------------------------------
    result = process_behavioral_window(
        window=window,
        session=session,
    )

    # ---------------------------------------------------------
    # 4. RETURN PROCESSING RESULT
    # ---------------------------------------------------------
    return result