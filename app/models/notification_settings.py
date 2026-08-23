from sqlalchemy import Column, Integer, String, Boolean
from app.db.session import Base

class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String(255), unique=True, nullable=False, index=True)
    email_alerts_enabled = Column(Boolean, default=True, nullable=False)