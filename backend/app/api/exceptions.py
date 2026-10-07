from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.employee import Employee
from app.models.exception import ExceptionAuthorization
from app.schemas.exception import (
    ExceptionCreate,
    ExceptionRead,
    ExceptionStatusUpdate,
)


router = APIRouter(
    prefix="/exceptions",
    tags=["Exception Authorizations"],
)


@router.post(
    "/",
    response_model=ExceptionRead,
    status_code=201,
)
def create_exception(
    exception_data: ExceptionCreate,
    session: Session = Depends(get_session),
):
    # -------------------------------------------------
    # 1. Verify employee
    # -------------------------------------------------

    employee = session.get(
        Employee,
        exception_data.employee_id,
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    if not employee.is_active:
        raise HTTPException(
            status_code=403,
            detail="Employee is inactive.",
        )

    # -------------------------------------------------
    # 2. Validate time range
    # -------------------------------------------------

    if exception_data.end_time <= exception_data.start_time:
        raise HTTPException(
            status_code=400,
            detail="end_time must be later than start_time.",
        )

    # -------------------------------------------------
    # 3. Create authorization
    # -------------------------------------------------

    exception = ExceptionAuthorization(
        employee_id=exception_data.employee_id,
        reason=exception_data.reason,
        authorized_by=exception_data.authorized_by,
        start_time=exception_data.start_time,
        end_time=exception_data.end_time,
        allowed_activity=exception_data.allowed_activity,
        status="ACTIVE",
    )

    session.add(exception)
    session.commit()
    session.refresh(exception)

    return exception


@router.get(
    "/employee/{employee_id}",
    response_model=list[ExceptionRead],
)
def get_employee_exceptions(
    employee_id: int,
    session: Session = Depends(get_session),
):
    employee = session.get(
        Employee,
        employee_id,
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    statement = (
        select(ExceptionAuthorization)
        .where(
            ExceptionAuthorization.employee_id
            == employee_id
        )
        .order_by(
            ExceptionAuthorization.start_time.desc()
        )
    )

    return list(session.exec(statement).all())


@router.patch(
    "/{exception_id}/status",
    response_model=ExceptionRead,
)
def update_exception_status(
    exception_id: int,
    status_data: ExceptionStatusUpdate,
    session: Session = Depends(get_session),
):
    exception = session.get(
        ExceptionAuthorization,
        exception_id,
    )

    if not exception:
        raise HTTPException(
            status_code=404,
            detail="Exception authorization not found.",
        )

    new_status = status_data.status.upper()

    if new_status not in {
        "ACTIVE",
        "REVOKED",
        "EXPIRED",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. Use ACTIVE, "
                "REVOKED, or EXPIRED."
            ),
        )

    exception.status = new_status

    session.add(exception)
    session.commit()
    session.refresh(exception)

    return exception