from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from app.models.schemas import UserRole, EventStatus
import enum

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(SQLAlchemyEnum(UserRole))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("Event", back_populates="user")

class Validation(Base):
    __tablename__ = "validations"

    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String)
    cep = Column(String)
    cnpj_data = Column(JSON)
    cep_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    scheduled_date = Column(DateTime)
    status = Column(SQLAlchemyEnum(EventStatus))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="events")

class RocketLaunch(Base):
    __tablename__ = "rocket_launches"

    id = Column(Integer, primary_key=True, index=True)
    mission_name = Column(String)
    launch_date = Column(DateTime)
    rocket_name = Column(String)
    launch_site = Column(String)
    mission_status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 