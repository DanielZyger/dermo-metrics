from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from datetime import datetime
from sqlalchemy.orm import relationship
from .base import Base
from app.constants.enum import GenderEnum

class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    description = Column(Text)
    gender = Column(Enum(GenderEnum))
    phone = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    fingerprints = relationship("Fingerprint", back_populates="volunteer")
    # analyses = relationship("Analyse", back_populates="patient")

# TODO ANALISAR IMPORTS CICLICOS 

