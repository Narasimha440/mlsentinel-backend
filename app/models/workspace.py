from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner_firebase_uid = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())