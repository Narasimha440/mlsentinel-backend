from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    firebase_uid = Column(String(255), nullable=False, index=True)
    label = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked = Column(Boolean, default=False, nullable=False)
    default_ml_model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=True)