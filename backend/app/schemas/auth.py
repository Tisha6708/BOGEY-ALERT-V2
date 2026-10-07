from pydantic import BaseModel


class AgentLoginRequest(BaseModel):
    device_code: str
    device_credential: str


class AgentLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    device_id: int
    employee_id: int