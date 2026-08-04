from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.schedule_settings import ScheduleSettings, ScheduleFrequency
from app.models.ml_model import MLModel
from app.models.project import Project
from app.models.workspace import Workspace
from app.auth.firebase import verify_firebase_token

router = APIRouter()

class ScheduleRequest(BaseModel):
    model_id: int
    frequency: ScheduleFrequency

def _verify_ownership(db, model_id, uid):
    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    project = db.query(Project).filter(Project.id == model.project_id).first()
    workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
    if workspace.owner_firebase_uid != uid:
        raise HTTPException(status_code=403, detail="Not authorized")
    return model

@router.post("/settings/schedule")
def set_schedule(req: ScheduleRequest, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    _verify_ownership(db, req.model_id, user["uid"])

    existing = db.query(ScheduleSettings).filter(ScheduleSettings.ml_model_id == req.model_id).first()

    if existing:
        existing.frequency = req.frequency
    else:
        existing = ScheduleSettings(ml_model_id=req.model_id, frequency=req.frequency)
        db.add(existing)
    db.commit()
    return {"success": True, "frequency": req.frequency}

@router.get("/settings/schedule/{model_id}")
def get_schedule(model_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    _verify_ownership(db, model_id, user["uid"])
    setting = db.query(ScheduleSettings).filter(ScheduleSettings.ml_model_id == model_id).first()
    return {"frequency": setting.frequency if setting else "off"}