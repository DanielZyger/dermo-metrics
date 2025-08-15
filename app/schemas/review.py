from pydantic import BaseModel
from datetime import datetime

class ReviewBase(BaseModel):
    patient_id: int
    user_id: int
    sqtl: int
    delta_indice: int

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    sqtl: int | None = None
    delta_indice: int | None = None

class ReviewOut(ReviewBase):
    id: int
    date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
