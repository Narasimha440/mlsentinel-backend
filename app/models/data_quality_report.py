from sqlalchemy import Column, Integer, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base

class DataQualityReport(Base):
    __tablename__ = "data_quality_reports"

    id = Column(Integer, primary_key=True, index=True)
    ml_model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False, index=True)
    summary = Column(JSON, nullable=False)
    findings = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)