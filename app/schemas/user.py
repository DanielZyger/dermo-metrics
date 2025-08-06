from pydantic import BaseModel
from datetime import datetime
from app.constants.enum import UserRoles

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRoles
    created_at: datetime

    class Config:
        orm_mode = True
