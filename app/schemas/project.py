from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProjectBase(BaseModel):
    """Schema base para Project"""
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    """Schema para criação de Project"""
    pass

class ProjectUpdate(ProjectBase):
    """Schema para atualização de Project"""
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectOut(ProjectBase):
    """Schema para resposta de Project"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True