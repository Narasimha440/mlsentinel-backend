from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.session import get_db
from app.auth.firebase import verify_firebase_token
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.ml_model import MLModel
from app.models.run_history import RunHistory
from app.analysisengine.rule_engine import RuleEngine

router = APIRouter()

@router.get("/monitoring")
def get_dashboard_monitoring(
    limit: int = 14,
    current_user: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db)
):
    user_models = (
        db.query(MLModel.id, MLModel.name, Project.name.label("project_name"))
        .join(Project, MLModel.project_id == Project.id)
        .join(Workspace, Project.workspace_id == Workspace.id)
        .filter(Workspace.owner_firebase_uid == current_user["uid"])
        .all()
    )

    monitoring_data = []


    for model_id, model_name, project_name in user_models:

        recent_runs = (
            db.query(RunHistory)
            .filter(RunHistory.ml_model_id == model_id)
            .order_by(desc(RunHistory.created_at))
            .limit(limit)
            .all()
        )

        chart_data = []
        for run in reversed(recent_runs):
            matched_rules = RuleEngine.evaluate(run.metrics)
            
            status = (
                "Critical" if any(r.severity.value == "critical" for r in matched_rules)
                else "Warning" if matched_rules
                else "Healthy"
            )


            chart_data.append({
                "id": run.id,
                "created_at": run.created_at,
                "health_score": run.health_score,
                "status": status,
                "metrics": run.metrics,
            })

        monitoring_data.append({
            "model_id": model_id,
            "model_name": model_name,
            "project_name": project_name,
            "trend": chart_data
        })

    return {"monitoring": monitoring_data}