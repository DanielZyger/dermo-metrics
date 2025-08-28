from sqlalchemy import Column, Integer, ForeignKey, Enum, LargeBinary, DateTime, Text
from datetime import datetime
from sqlalchemy.orm import relationship
from app.models.volunteer import Volunteer
from .base import Base
from app.constants.enum import HandEnum, FingerEnum, PatternEnum

class Fingerprint(Base):
    __tablename__ = "fingerprints"

    id = Column(Integer, primary_key=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"), nullable=False)

    hand = Column(Enum(HandEnum), nullable=False)
    finger = Column(Enum(FingerEnum), nullable=False)
    pattern_type = Column(Enum(PatternEnum))

    delta = Column(Integer)
    image_data = Column(LargeBinary)
    image_filtered = Column(LargeBinary)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    volunteer = relationship("Volunteer", back_populates="fingerprints")