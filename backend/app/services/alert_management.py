import json
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.alert import Alert


VALID_STATUSES = {
    "PENDING",
    "UNDER_REVIEW",
    "CONFIRMED",
    "DISMISSED",
}


def _to_alert_dict(alert: Alert) -> dict:
    """
    Convert the database Alert model into
    the structure expected by the API.
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
        "created_at": alert.created_at,
        "reviewed_at": alert.reviewed_at,
        "analyst_decision": alert.analyst_decision,
        "analyst_notes": alert.analyst_notes,
    }


def get_alerts(
    session: Session,
    status: str | None = None,
) -> list[dict]:
    """
    Retrieve alerts, optionally filtered by status.
    """

    statement = select(Alert).order_by(
        Alert.created_at.desc()
    )

    if status:
        status = status.upper()

        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid alert status: {status}"
            )

        statement = statement.where(
            Alert.status == status
        )

    alerts = session.exec(statement).all()

    return [
        _to_alert_dict(alert)
        for alert in alerts
    ]


def get_alert(
    alert_id: int,
    session: Session,
) -> dict | None:
    """
    Retrieve a single alert by ID.
    """

    alert = session.get(Alert, alert_id)

    if not alert:
        return None

    return _to_alert_dict(alert)


def review_alert(
    alert_id: int,
    status: str,
    analyst_notes: str | None,
    session: Session,
) -> dict | None:
    """
    Update the lifecycle state of an alert.
    """

    status = status.upper()

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid alert status: {status}"
        )

    alert = session.get(Alert, alert_id)

    if not alert:
        return None

    # A final decision should not silently
    # be changed later.
    if alert.status in {"CONFIRMED", "DISMISSED"}:
        raise ValueError(
            "This alert has already been finalized."
        )

    alert.status = status

    if status in {"CONFIRMED", "DISMISSED"}:
        alert.reviewed_at = datetime.now(timezone.utc)
        alert.analyst_decision = status
        alert.analyst_notes = analyst_notes

    elif status == "UNDER_REVIEW":
        alert.analyst_notes = analyst_notes

    session.add(alert)
    session.commit()
    session.refresh(alert)

    return _to_alert_dict(alert)