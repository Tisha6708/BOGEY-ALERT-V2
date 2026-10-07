import asyncio
import json

from sqlmodel import Session, select

from app.detection.risk_engine import RiskResult
from app.models.alert import Alert
from app.models.behavioral_window import BehavioralWindow
from app.models.device import Device
from app.services.websocket_manager import manager


def _to_alert_payload(alert: Alert) -> dict:
    """
    Convert an Alert database model into a JSON-safe
    payload for the REST API and WebSocket stream.
    """

    try:
        reasons = json.loads(alert.reasons_json)
    except (json.JSONDecodeError, TypeError):
        reasons = []

    return {
        "id": alert.id,
        "employee_id": alert.employee_id,
        "device_id": alert.device_id,
        "behavioral_window_id": alert.behavioral_window_id,
        "risk_score": alert.risk_score,
        "risk_level": alert.risk_level,
        "status": alert.status,
        "reasons": reasons,
        "created_at": (
            alert.created_at.isoformat()
            if alert.created_at
            else None
        ),
        "reviewed_at": (
            alert.reviewed_at.isoformat()
            if alert.reviewed_at
            else None
        ),
        "analyst_decision": alert.analyst_decision,
        "analyst_notes": alert.analyst_notes,
    }


def _broadcast_alert(alert: Alert):
    """
    Broadcast an alert after it has been successfully
    persisted.

    Detection remains synchronous; the WebSocket notification
    is best-effort and does not affect database processing.
    """

    payload = {
        "type": "SECURITY_ALERT",
        "alert": _to_alert_payload(alert),
    }

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No active async event loop in this execution context.
        return

    loop.create_task(
        manager.broadcast(payload)
    )


def create_alert_if_required(
    window: BehavioralWindow,
    device: Device,
    risk_result: RiskResult,
    session: Session,
):
    """
    Create or update an alert for a behavioral window.

    A behavioral window should have at most one active alert record.

    If the same window is analyzed again and its risk context changes
    because of authorization, policy, or detection changes, an existing
    non-finalized alert is updated.

    Finalized alerts are preserved for auditability.
    """

    # ---------------------------------------------------------
    # 1. LOW RISK
    # ---------------------------------------------------------
    if risk_result.risk_level == "LOW":
        return None

    # ---------------------------------------------------------
    # 2. CHECK FOR EXISTING ALERT
    # ---------------------------------------------------------
    existing_alert = session.exec(
        select(Alert).where(
            Alert.behavioral_window_id == window.id
        )
    ).first()

    # ---------------------------------------------------------
    # 3. CREATE NEW ALERT
    # ---------------------------------------------------------
    if existing_alert is None:
        alert = Alert(
            employee_id=device.employee_id,
            device_id=device.id,
            behavioral_window_id=window.id,
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level,
            status="PENDING",
            reasons_json=json.dumps(
                risk_result.reasons
            ),
        )

        session.add(alert)
        session.commit()
        session.refresh(alert)

        # Database commit succeeded, so notify analysts.
        _broadcast_alert(alert)

        return alert

    # ---------------------------------------------------------
    # 4. PRESERVE FINALIZED ALERTS
    # ---------------------------------------------------------
    if existing_alert.status in {
        "CONFIRMED",
        "DISMISSED",
    }:
        return existing_alert

    # ---------------------------------------------------------
    # 5. UPDATE NON-FINALIZED ALERT
    # ---------------------------------------------------------
    existing_alert.risk_score = risk_result.risk_score
    existing_alert.risk_level = risk_result.risk_level
    existing_alert.reasons_json = json.dumps(
        risk_result.reasons
    )

    session.add(existing_alert)
    session.commit()
    session.refresh(existing_alert)

    # Notify analysts about the updated risk context.
    _broadcast_alert(existing_alert)

    return existing_alert