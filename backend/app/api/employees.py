from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeRead


router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


@router.post(
    "/",
    response_model=EmployeeRead,
    status_code=201,
)
def create_employee(
    employee_data: EmployeeCreate,
    session: Session = Depends(get_session),
):
    existing_employee = session.exec(
        select(Employee).where(
            Employee.employee_code
            == employee_data.employee_code
        )
    ).first()

    if existing_employee:
        raise HTTPException(
            status_code=409,
            detail="Employee code already exists",
        )

    employee = Employee(
        employee_code=employee_data.employee_code,
        role=employee_data.role,
        department=employee_data.department,
        manager_id=employee_data.manager_id,
    )

    session.add(employee)
    session.commit()
    session.refresh(employee)

    return employee


@router.get(
    "/",
    response_model=list[EmployeeRead],
)
def get_employees(
    session: Session = Depends(get_session),
):
    statement = select(Employee).order_by(
        Employee.id
    )

    employees = session.exec(statement).all()

    return list(employees)


@router.get(
    "/{employee_id}",
    response_model=EmployeeRead,
)
def get_employee(
    employee_id: int,
    session: Session = Depends(get_session),
):
    employee = session.get(Employee, employee_id)

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    return employee