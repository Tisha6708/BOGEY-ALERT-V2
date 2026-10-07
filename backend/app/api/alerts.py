from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.alert import AlertRead, AlertReviewRequest
from app.services.alert_management import (
    get_alert,
    get_alerts,
    review_alert,
)
from app.services.investigation_service import get_alert_investigation


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.get("/", response_model=list[AlertRead])
def list_alerts(
    status: str | None = Query(
        default=None,
        description="Filter by alert status.",
    ),
    session: Session = Depends(get_session),
):
    try:
        return get_alerts(
            session=session,
            status=status,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get("/{alert_id}/investigation")
def investigate_alert(
    alert_id: int,
    session: Session = Depends(get_session),
):
    try:
        result = get_alert_investigation(
            alert_id=alert_id,
            session=session,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    return result


@router.get("/{alert_id}", response_model=AlertRead)
def retrieve_alert(
    alert_id: int,
    session: Session = Depends(get_session),
):
    alert = get_alert(
        alert_id=alert_id,
        session=session,
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    return alert


@router.patch(
    "/{alert_id}/review",
    response_model=AlertRead,
)
def review_existing_alert(
    alert_id: int,
    review_data: AlertReviewRequest,
    session: Session = Depends(get_session),
):
    try:
        alert = review_alert(
            alert_id=alert_id,
            status=review_data.status,
            analyst_notes=review_data.analyst_notes,
            session=session,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    return alert