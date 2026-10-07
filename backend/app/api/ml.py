from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.models.employee import Employee
from app.services.ml_training import train_employee_detector


router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning"],
)


@router.post("/train/{employee_id}")
def train_employee_model(
    employee_id: int,
    session: Session = Depends(get_session),
):
    employee = session.get(Employee, employee_id)

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found.",
        )

    try:
        result = train_employee_detector(
            employee_id=employee_id,
            session=session,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message": "Behavioral model trained successfully.",
        "employee_id": employee_id,
        "artifact": result,
    }