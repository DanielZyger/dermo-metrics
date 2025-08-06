from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum
from datetime import datetime
from sqlalchemy.orm import relationship
from .base import Base
from app.constants.enum import GenderEnum

class Analyse(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer , ForeignKey("patients.id"), nullable=False)
    user_id = Column(Integer , ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sqtl = Column(Integer , nullable=False)
    delta_indice = Column(Integer , nullable=False)

    patient = relationship("Patient", back_populates="analyses")
    user = relationship("User", back_populates="analyses")

