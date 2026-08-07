from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Any

from app.db.session import get_db
from app.auth.firebase import verify_firebase_token
from app.models.ml_model import MLModel
from app.models.project import Project
from app.models.alert import Alert
from app.models.workspace import Workspace
from app.analysisengine.rule_engine import RuleEngine

router = APIRouter()


class FeatureData(BaseModel):
    baseline: List[float]
    current: List[float]

class DriftAnalysisRequest(BaseModel):
    features: Dict[str, FeatureData]


@router.post("/models/{model_id}/drift")
def analyze_model_drift(
    model_id: int,
    payload: DriftAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_firebase_token)
):

    model = (
        db.query(MLModel)
        .join(Project, MLModel.project_id == Project.id)
        .join(Workspace, Project.workspace_id == Workspace.id)
        .filter(MLModel.id == model_id, Workspace.owner_firebase_uid == current_user["uid"])
        .first()
    )

    if not model:
        raise HTTPException(status_code=404, detail="Model not found or access denied")

    feature_payloads = {
        name: {"baseline": data.baseline, "current": data.current}
        for name, data in payload.features.items()
    }

    drift_results = RuleEngine.evaluate_drift(feature_payloads)


    created_alerts = []

    for result in drift_results:
        new_alert = Alert(
            ml_model_id = model.id,
            severity = result["severity"],
            message = result["message"],
            acknowledged=False
        )
        db.add(new_alert)
        created_alerts.append(result)


    if created_alerts:
        db.commit()


    return {
        "status": "success",
        "feature_analyzed": len(payload.features),
        "drift_alerts_created": len(created_alerts),
        "details": created_alerts
    }