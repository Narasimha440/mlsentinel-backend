from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.ml_model import MLModel
from app.models.run_history import RunHistory
from app.auth.firebase import verify_firebase_token

router = APIRouter()


@router.get("/projects")

def get_projects(db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    owner_uid = user["uid"]

    workspace = db.query(Workspace).filter(Workspace.owner_firebase_uid == owner_uid).first()

    if not workspace:
        return {"projects": []}

    projects = db.query(Project).filter(Project.workspace_id == workspace.id).all()

    result = []

    for project in projects:
        models = db.query(MLModel).filter(MLModel.project_id == project.id).all()

        model_list = []

        for model in models:
            latest_run = (
                db.query(RunHistory)
                .filter(RunHistory.ml_model_id == model.id)
                .order_by(RunHistory.created_at.desc())
                .first()
            )

            model_list.append({
                "model_id": model.id,
                "name": model.name,
                "health_score": latest_run.health_score if latest_run else None,
                "last_run_at": latest_run.created_at.isoformat() if latest_run else None,
                "total_runs": db.query(RunHistory).filter(RunHistory.ml_model_id == model.id).count(),
            })

        result.append({
            "project_id": project.id,
            "name": project.name,
            "models": model_list,
        })
    return {"projects": result}