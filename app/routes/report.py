"""
report api route
"""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.api_key import verify_api_key
from app.db.session import get_db
from app.models.api_key import APIKey
from app.models.ml_model import MLModel
from app.models.project import Project
from app.models.report import ReportRequest
from app.services.report_service import ReportService

router = APIRouter()

class AutoReportRequest(BaseModel):
    metrics: dict[str, Any]

@router.post("/report")
def receive_report(report: ReportRequest, owner_uid: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    return ReportService.process_method(report, db, owner_uid)

@router.post("/report/auto")
def receive_auto_report(
    report: AutoReportRequest,
    owner_uid: str = Depends(verify_api_key),
    x_api_key: str = Header(...),
    db: Session = Depends(get_db)
):

    api_key = (
        db.query(APIKey)
        .filter(
            APIKey.key == x_api_key,
            APIKey.firebase_uid == owner_uid,
            APIKey.revoked == False,
        )
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key not found.",
        )

    if not api_key.default_ml_model_id:
        raise HTTPException(
            status_code=400,
            detail="This API key is not associated with a default model.",
        )

    model = (
        db.query(MLModel)
        .filter(MLModel.id == api_key.default_ml_model_id)
        .first()
    )

    if not model:
        raise HTTPException(
            status_code=404,
            detail="The model associated with this API key was not found.",
        )

    project = (
        db.query(Project)
        .filter(Project.id == model.project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="The project associated with this model was not found.",
        )

    full_report = ReportRequest(
        project=project.name,
        model=model.name,
        metrics=report.metrics,
    )

    return ReportService.process_method(
        full_report,
        db,
        owner_uid,
    )