from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base

class GithubInstallation(Base):
    __tablename__ = "github_installations"


    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(255), nullable=False, index=True)
    installation_id = Column(String(255), nullable=False)
    account_login = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())