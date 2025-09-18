from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text, Float, Enum
from datetime import datetime
from sqlalchemy.orm import relationship
from .base import Base
from app.constants.enum import GenderEnum, VolunteerStatuses

class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    description = Column(Text)
    weight = Column(Float)
    height = Column(Float)
    status = Column(Enum(VolunteerStatuses), default=VolunteerStatuses.pending)
    gender = Column(Enum(GenderEnum))
    phone = Column(String)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    fingerprints = relationship("Fingerprint", back_populates="volunteer")
    project = relationship("Project", back_populates="volunteers")


