from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class RunHistory(Base):
    __tablename__ = "run_history"

    id = Column(Integer, primary_key=True, index=True)
    project = Column(String(255), nullable=False, index=True)
    model = Column(String(255), nullable=False, index=True)
    metrics = Column(JSON, nullable=False)
    health_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)