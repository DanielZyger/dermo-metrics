from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.constants.enum import GenderEnum, VolunteerStatuses
from app.schemas.fingerprint import FingerprintOut

class VolunteerCreate(BaseModel):
    name: str
    age: Optional[int]
    description: Optional[str]
    gender: Optional[GenderEnum]
    weight: Optional[float]
    height: Optional[float]
    phone: Optional[str]
    project_id: Optional[int] = None

class VolunteerOut(BaseModel):
    id: int
    name: str
    age: Optional[int]
    description: Optional[str]
    gender: Optional[GenderEnum]
    phone: Optional[str]
    project_id: int
    weight: Optional[float]
    height: Optional[float]
    status: Optional[VolunteerStatuses]
    created_at: datetime
    updated_at: datetime
    fingerprints: List[FingerprintOut] = []

    class Config:
        orm_mode = True