from typing import Dict, List
from sqlalchemy.orm import Session
from app.models.run_history import RunHistory

class RunHistoryStorage:
    def __init__(self, db: Session):
        self.db = db

    def save(self, project: str, model:str, metrics: Dict[str, float], health_score: float = None):
        entry = RunHistory(project=project, model=model, metrics=metrics, health_score=health_score)
        self.db.add(entry)
        self.db.commit()

    def get_recent(self, project: str, model: str, limit: int = 10) -> List[Dict[str, float]]:
        rows = (
            self.db.query(RunHistory)
            .filter(RunHistory.project == project, RunHistory.model == model)
            .order_by(RunHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        return [row.metrics for row in reversed(rows)]