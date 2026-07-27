from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.run_history import RunHistory
from app.services.hierarchy_service import HierarchyService
from app.auth.firebase import verify_firebase_token

router = APIRouter()

@router.get("/history/{project}/{model}")
def get_history(
    project: str,
    model: str,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token),
):
    owner_uid = user["uid"]
    ml_model_id = HierarchyService.find_model_id_for_owner(db, owner_uid, project, model)

    if ml_model_id is None:
        raise HTTPException(status_code=404, detail="Project/model not found for this user")

    rows = (
        db.query(RunHistory)
        .filter(RunHistory.ml_model_id == ml_model_id)
        .order_by(RunHistory.created_at.desc())
        .limit(limit)
        .all()
    )

    rows = list(reversed(rows))

    return {
        "project": project,
        "model": model,
        "count": len(rows),
        "runs": [
            {
                "id": r.id,
                "metrics": r.metrics,
                "health_score": r.health_score,
                "created_at": r.created_at.isoformat(),
            }

            for r in rows
        ],
    }