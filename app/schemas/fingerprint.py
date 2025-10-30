from pydantic import BaseModel, field_serializer
from datetime import datetime
from typing import Optional
from app.constants.enum import HandEnum, FingerEnum, PatternEnum
from app.utils.to_base_64 import to_base64

class FingerprintCreate(BaseModel):
    volunteer_id: int
    hand: HandEnum
    finger: FingerEnum
    pattern_type: Optional[PatternEnum]
    delta: Optional[int]
    image_processed: Optional[bytes]
    number_of_lines: Optional[int]
    notes: Optional[str]

class FingerprintOut(BaseModel):
    id: int
    volunteer_id: int
    hand: HandEnum
    finger: FingerEnum
    pattern_type: Optional[PatternEnum]
    delta: Optional[int]
    notes: Optional[str]
    number_of_lines: Optional[int]
    image_data: Optional[bytes]
    image_filtered: Optional[bytes]
    image_processed: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

    @field_serializer("image_data", "image_filtered", "image_processed")
    def encode_base64(self, value: Optional[bytes], _info):
        return to_base64(value)