from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.exception import ExceptionAuthorization


def _normalize_utc(value: datetime) -> datetime:
    """
    Normalize datetime to timezone-aware UTC.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def get_active_exception(
    employee_id: int,
    activity_time: datetime,
    session: Session,
    activity: str | None = None,
) -> ExceptionAuthorization | None:
    """
    Find an active authorization covering the activity timestamp.

    Authorization does NOT disable ML detection.
    It only provides authorization context to the risk engine.
    """

    activity_time = _normalize_utc(activity_time)

    exceptions = session.exec(
        select(ExceptionAuthorization)
        .where(
            ExceptionAuthorization.employee_id == employee_id,
            ExceptionAuthorization.status == "ACTIVE",
        )
        .order_by(
            ExceptionAuthorization.start_time.desc()
        )
    ).all()

    for exception in exceptions:
        start_time = _normalize_utc(exception.start_time)
        end_time = _normalize_utc(exception.end_time)

        # Timestamp must be inside authorization window.
        if not (start_time <= activity_time <= end_time):
            continue

        # If activity was supplied, authorization must match it.
        if activity:
            allowed = exception.allowed_activity.strip().lower()
            actual = activity.strip().lower()

            if allowed != actual:
                continue

        return exception

    return None