from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class RocketLaunch(Base):
    __tablename__ = "rocket_launches"

    id = Column(Integer, primary_key=True, index=True)
    launch_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    launch_date = Column(DateTime, nullable=False)
    rocket_name = Column(String, nullable=False)
    rocket_type = Column(String, nullable=False)
    launch_site = Column(String, nullable=False)
    mission_name = Column(String)
    mission_details = Column(JSON)
    payload_mass = Column(Float)
    orbit = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    user = relationship("User", back_populates="rocket_launches") 