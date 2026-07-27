from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.run_history import RunHistory

class RunHistoryStorage:
    def __init__(self, db: Session):
        self.db = db

    def save(self, ml_model_id: int, metrics: Dict[str, float], health_score: float = None):
        entry = RunHistory(ml_model_id=ml_model_id, metrics=metrics, health_score=health_score)
        self.db.add(entry)
        self.db.commit()

    def get_recent(self, ml_model_id: int, limit: int = 10) -> List[Dict[str, float]]:
        rows = (
            self.db.query(RunHistory)
            .filter(RunHistory.ml_model_id == ml_model_id)
            .order_by(RunHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return [row.metrics for row in reversed(rows)]