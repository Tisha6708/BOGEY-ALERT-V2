from typing import Optional

from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    employee_code: str
    role: str
    department: str
    manager_id: Optional[int] = None


class EmployeeRead(BaseModel):
    id: int
    employee_code: str
    role: str
    department: str
    manager_id: Optional[int]
    is_active: bool