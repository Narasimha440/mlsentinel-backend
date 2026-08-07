from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any

from app.db.session import get_db
from app.auth.api_key import verify_api_key
from app.auth.firebase import verify_firebase_token
from app.services.hierarchy_service import HierarchyService
from app.models.data_quality_report import DataQualityReport
from app.analysisengine.data_quality import DataQualityEngine

router = APIRouter()


class DataQualityRequest(BaseModel):
    project: str
    model: str
    summary: Dict[str, Any]


@router.post("/data-quality")
def submit_data_quality(req: DataQualityRequest, owner_uid: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    ml_model_id = HierarchyService.resolve_model_id(db, owner_uid, req.project, req.model)

    findings = DataQualityEngine.evaluate(req.summary)

    findings_json = [
        {"column": f.column, "issue": f.issue, "severity": f.severity.value, "detail": f.detail}
        for f in findings
    ]

    report = DataQualityReport(
        ml_model_id=ml_model_id,
        summary=req.summary,
        findings=findings_json,
    )
    db.add(report)
    db.commit()

    return {
        "success": True,
        "row_count": req.summary.get("row_count"),
        "column_count": req.summary.get("column_count"),
        "findings": findings_json,
    }

@router.get("/dashboard/data-quality")
def get_dashboard_data_quality(
    model_id: int = None,
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token)
):
    from app.models.workspace import Workspace
    from app.models.project import Project
    from app.models.ml_model import MLModel

    workspace = db.query(Workspace).filter(Workspace.owner_firebase_uid == user["uid"]).first()

    if not workspace:
        return {"reports": []}

    project_ids = [p.id for p in db.query(Project).filter(Project.workspace_id == workspace.id).all()]
    all_models = db.query(MLModel).filter(MLModel.project_id.in_(project_ids)).all()

    models = [m for m in all_models if m.id == model_id] if model_id else all_models
    project_by_id = {p.id: p for p in db.query(Project).filter(Project.id.in_(project_ids)).all()}

    reports = []

    for model in models:
        latest = (
            db.query(DataQualityReport)
            .filter(DataQualityReport.ml_model_id == model.id)
            .order_by(DataQualityReport.created_at.desc())
            .first()
        )

        if not latest:
            continue

        project = project_by_id.get(model.project_id)


        reports.append({
            "model_id": model.id,
            "model_name": model.name,
            "project_name": project.name if project else None,
            "row_count": latest.summary.get("row_count"),
            "column_count": latest.summary.get("column_count"),
            "duplicate_row_percentage": latest.summary.get("duplicate_row_percentage"),
            "findings": latest.findings or [],
            "columns": latest.summary.get("columns", {}),
            "checked_at": latest.created_at.isoformat(),
        })
        
    return {"reports": reports}