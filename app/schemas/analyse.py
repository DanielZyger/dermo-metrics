from pydantic import BaseModel
from datetime import datetime

class AnalyseBase(BaseModel):
    patient_id: int
    user_id: int
    sqtl: int
    delta_indice: int

class AnalyseCreate(AnalyseBase):
    pass

class AnalyseUpdate(BaseModel):
    sqtl: int | None = None
    delta_indice: int | None = None

class AnalyseOut(AnalyseBase):
    id: int
    date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
