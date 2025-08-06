from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.constants.enum import GenderEnum

class PatientCreate(BaseModel):
    name: str
    age: Optional[int]
    description: Optional[str]
    gender: Optional[GenderEnum]
    phone: Optional[str]

class PatientOut(BaseModel):
    id: int
    name: str
    age: Optional[int]
    gender: Optional[GenderEnum]
    phone: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
