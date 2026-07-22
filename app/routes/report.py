"""
report api route
"""

from fastapi import APIRouter, Depends
from app.auth.api_key import verify_api_key
from app.models.report import ReportRequest
from app.services.report_service import ReportService

router = APIRouter()

@router.post("/report")
def receive_report(report: ReportRequest, api_key: str = Depends(verify_api_key)):
    return ReportService.process_method(report)