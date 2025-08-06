from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .base import Base
from app.constants.enum import UserRoles

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(UserRoles, nullable=False, default=UserRoles.researcher)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
