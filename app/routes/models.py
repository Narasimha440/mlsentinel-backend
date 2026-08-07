from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.auth.firebase import verify_firebase_token
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.ml_model import MLModel
from app.models.schedule_settings import ScheduleSettings
from app.models.run_history import RunHistory
from app.analysisengine.rule_engine import RuleEngine

router = APIRouter()

@router.get("/dashboard/models")
def get_dashboard_models(current_user: dict = Depends(verify_firebase_token), db: Session = Depends(get_db)):

    results = (
        db.query(MLModel, Project.name.label("project_name"), ScheduleSettings)
        .join(Project, MLModel.project_id == Project.id)
        .join(Workspace, Project.workspace_id == Workspace.id)
        .outerjoin(ScheduleSettings, MLModel.id == ScheduleSettings.ml_model_id)
        .filter(Workspace.owner_firebase_uid == current_user["uid"])
        .order_by(desc(MLModel.created_at))
        .all()
    )

    models_data = []
    for model, project_name, schedule in results:

        latest_run = (
            db.query(RunHistory)
            .filter(RunHistory.ml_model_id == model.id)
            .order_by(RunHistory.created_at.desc())
            .first()
        )

        health_score = latest_run.health_score if latest_run else None
        matched_rules = RuleEngine.evaluate(latest_run.metrics) if latest_run else []

        status = (
            "Critical" if any(r.severity.value == "critical" for r in matched_rules)
            else "Warning" if matched_rules
            else "Healthy"
        )

        models_data.append({
            "id": model.id,
            "name": model.name,
            "project_id": model.project_id,
            "project_name": project_name,
            "health_score": health_score,
            "status": status,
            "schedule_frequency": schedule.frequency if schedule else "off",
            "last_run_at": schedule.last_run_at if schedule else None,
            "created_at": model.created_at
        })

    return {"models": models_data}