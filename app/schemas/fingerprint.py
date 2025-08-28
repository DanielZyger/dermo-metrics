from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.constants.enum import HandEnum, FingerEnum, PatternEnum

class FingerprintCreate(BaseModel):
    volunteer_id: int
    hand: HandEnum
    finger: FingerEnum
    pattern_type: Optional[PatternEnum]
    delta: Optional[int]
    notes: Optional[str]

class FingerprintOut(BaseModel):
    id: int
    volunteer_id: int
    hand: HandEnum
    finger: FingerEnum
    pattern_type: Optional[PatternEnum]
    delta: Optional[int]
    notes: Optional[str]
    image_data: Optional[str]
    image_filtered: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
