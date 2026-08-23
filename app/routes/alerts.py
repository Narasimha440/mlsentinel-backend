from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.ml_model import MLModel
from app.models.alert import Alert
from app.auth.firebase import verify_firebase_token


router = APIRouter()


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    workspace = db.query(Workspace).filter(Workspace.owner_firebase_uid == user["uid"]).first()
    if not workspace:
        return {"alerts": [], "unacknowledged_count": 0}

    project_ids = [p.id for p in db.query(Project).filter(Project.workspace_id == workspace.id).all()]

    if not project_ids:
        return {
            "alerts": [],
            "unacknowledged_count": 0,
        }
    
    model_ids = [
        m.id
        for m in db.query(MLModel)
        .filter(MLModel.project_id.in_(project_ids))
        .all()
    ]

    if not model_ids:
        return {
            "alerts": [],
            "unacknowledged_count": 0,
        }

    alerts = (
        db.query(Alert)
        .filter(Alert.ml_model_id.in_(model_ids))
        .order_by(Alert.created_at.desc())
        .limit(50)
        .all()
    )


    unacknowledged_count = sum(1 for alert in alerts if not alert.acknowledged)

    return {
        "alerts": [
            {"id": a.id, "severity": a.severity, "message": a.message, "acknowledged": a.acknowledged, "created_at": a.created_at.isoformat()}
            for a in alerts
        ],
        "unacknowledged_count": unacknowledged_count
    }

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db), user: dict = Depends(verify_firebase_token)):
    workspace = (
        db.query(Workspace)
        .filter(
            Workspace.owner_firebase_uid == user["uid"]
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=404,
            detail="Workspace not found",
        )

    project_ids = [
        p.id
        for p in db.query(Project)
        .filter(Project.workspace_id == workspace.id)
        .all()
    ]

    model_ids = [
        m.id
        for m in db.query(MLModel)
        .filter(MLModel.project_id.in_(project_ids))
        .all()
    ]

    alert = (
        db.query(Alert)
        .filter(
            Alert.id == alert_id,
            Alert.ml_model_id.in_(model_ids),
        )
        .first()
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )
    alert.acknowledged = True
    db.commit()

    return {
        "success": True,
        "alert_id": alert.id,
    }