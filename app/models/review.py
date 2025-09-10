from sqlalchemy import Column, Integer, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from .base import Base

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer , ForeignKey("volunteers.id"), nullable=False)
    user_id = Column(Integer , ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sqtl = Column(Integer , nullable=False)
    delta_indice = Column(Integer , nullable=False)

    # volunteer = relationship("Volunteer", back_populates="reviews")

