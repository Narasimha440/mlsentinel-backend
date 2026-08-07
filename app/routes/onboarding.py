from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.ml_model import MLModel
from app.models.run_history import RunHistory
from app.services.hierarchy_service import HierarchyService
from app.auth.firebase import verify_firebase_token

router = APIRouter()


@router.get("/onboarding/status")
def get_onboarding_status(db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    """
    Tells the frontend exactly where the user is in the setup flow,
    so it knows which onboarding step to show (or skip straight to the dashboard).
    """
    workspace = db.query(Workspace).filter(Workspace.owner_firebase_uid == user["uid"]).first()
    if not workspace:
        return {"step": "workspace"}

    project = db.query(Project).filter(Project.workspace_id == workspace.id).first()
    if not project:
        return {"step": "project", "workspace": {"id": workspace.id, "name": workspace.name}}

    model = db.query(MLModel).filter(MLModel.project_id == project.id).first()
    if not model:
        return {
            "step": "model",
            "workspace": {"id": workspace.id, "name": workspace.name},
            "project": {"id": project.id, "name": project.name},
        }

    has_run = db.query(RunHistory).filter(RunHistory.ml_model_id == model.id).first() is not None

    return {
        "step": "waiting_for_first_report" if not has_run else "complete",
        "workspace": {"id": workspace.id, "name": workspace.name},
        "project": {"id": project.id, "name": project.name},
        "model": {"id": model.id, "name": model.name},
    }


class CreateWorkspaceRequest(BaseModel):
    name: str


@router.post("/onboarding/workspace")
def create_workspace(req: CreateWorkspaceRequest, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Workspace name is required")
    try:
        workspace = HierarchyService.create_workspace(db, user["uid"], req.name.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": workspace.id, "name": workspace.name}


class CreateProjectRequest(BaseModel):
    name: str


@router.post("/onboarding/project")
def create_project(req: CreateProjectRequest, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    workspace = db.query(Workspace).filter(Workspace.owner_firebase_uid == user["uid"]).first()
    if not workspace:
        raise HTTPException(status_code=400, detail="Create a workspace first")
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    try:
        project = HierarchyService.create_project(db, workspace.id, req.name.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": project.id, "name": project.name}


class CreateModelRequest(BaseModel):
    project_id: int
    name: str


@router.post("/onboarding/model")
def create_model(req: CreateModelRequest, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if not workspace or workspace.owner_firebase_uid != user["uid"]:
        raise HTTPException(status_code=403, detail="Not authorized for this project")

    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Model name is required")

    try:
        model = HierarchyService.create_model(db, req.project_id, req.name.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": model.id, "name": model.name}

@router.post("/models/quick-add")
def quick_add_model(req: CreateModelRequest, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):

    project = db.query(Project).filter(Project.id == req.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project no found")

    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if not workspace or workspace.owner_firebase_uid != user["uid"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    existing = db.query(MLModel).filter(MLModel.project_id == req.project_id, MLModel.name == req.name.strip()).first()
    if existing:
        return {"id": existing.id, "name": existing.name}

    model = MLModel(project_id=req.project_id, name=req.name.strip())
    db.add(model)
    db.commit()
    db.refresh(model)

    return {"id": model.id, "name": model.name}