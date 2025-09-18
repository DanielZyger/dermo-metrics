from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Enum
from datetime import datetime
from sqlalchemy.orm import relationship
from .base import Base
from app.constants.enum import UserRoles

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(Enum(UserRoles), nullable=False, default=UserRoles.researcher)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = relationship("UserProject", back_populates="user")

