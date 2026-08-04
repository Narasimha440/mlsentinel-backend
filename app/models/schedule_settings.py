from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.session import Base
import enum

class ScheduleFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    OFF = "off"

class ScheduleSettings(Base):
    __tablename__ = "schedule_settings"

    id = Column(Integer, primary_key=True, index=True)
    ml_model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False, unique=True, index=True)
    frequency = Column(SQLEnum(ScheduleFrequency), default=ScheduleFrequency.OFF, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())