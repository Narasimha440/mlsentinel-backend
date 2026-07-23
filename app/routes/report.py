"""
report api route
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.api_key import verify_api_key
from app.db.session import get_db
from app.models.report import ReportRequest
from app.services.report_service import ReportService

router = APIRouter()

@router.post("/report")
def receive_report(report: ReportRequest, api_key: str = Depends(verify_api_key), db: Session = Depends(get_db),):
    return ReportService.process_method(report, db)