from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.project import ProjectOut
from app.constants.enum import UserRoles

class UserCreate(BaseModel):
    name: str
    email: str
    project_id: Optional[int] = None
    role: Optional[UserRoles] = UserRoles.researcher

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRoles
    created_at: datetime
    projects: List[ProjectOut] = []

    class Config:
        orm_mode = True
