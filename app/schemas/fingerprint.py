from pydantic import BaseModel, field_serializer
from datetime import datetime
from typing import Optional
from app.constants.enum import HandEnum, FingerEnum, PatternEnum
from app.utils.to_base_64 import to_base64
from typing import List
class Point(BaseModel):
    x: float
    y: float

class FingerprintCreate(BaseModel):
    volunteer_id: int
    hand: HandEnum
    finger: FingerEnum
    notes: Optional[str]

class FingerprintOut(BaseModel):
    id: int
    volunteer_id: int
    hand: HandEnum
    finger: FingerEnum
    number_deltas: Optional[int]
    notes: Optional[str]
    pattern_type: Optional[PatternEnum]
    ridge_counts: Optional[int]
    core: Optional[Point]
    deltas: Optional[List[Point]]
    image_data: Optional[bytes]
    image_filtered: Optional[bytes]

    class Config:
        orm_mode = True

    @field_serializer("image_data", "image_filtered")
    def encode_base64(self, value: Optional[bytes], _info):
        return to_base64(value)