from typing import Dict, Optional
from .storage import RunHistoryStorage

LOSS_METRICS = {"val_loss", "loss", "train_loss"}

class TrendTracker:
    def __init__(self, storage: RunHistoryStorage, ml_model_id: int, window: int = 10):
        self.storage = storage
        self.ml_model_id = ml_model_id
        self.window = window

    def detect_drop(self, metric: str, drop_threshold: float = 0.10) -> bool:
        history = self.storage.get_recent(self.ml_model_id, self.window)
        if len(history) < 3:
            return False

        recent = [m.get(metric, 0) for m in history[:-1]]
        avg = sum(recent) / len(recent)
        current = history[-1].get(metric, 0)
        return (avg - current) > drop_threshold

    def detect_change(self, metric: str, threshold: float = 0.10) -> Optional[dict]:

        history = self.storage.get_recent(self.ml_model_id, self.window)

        if len(history) < 3:
            return None

        recent = [m.get(metric, 0) for m in history[:-1]]
        avg = sum(recent) / len(recent)
        current = history[-1].get(metric, 0)
        delta = current - avg

        if abs(delta) <= threshold:
            return None

        raw_direction = "rise" if delta > 0 else "drop"
        is_loss = metric in LOSS_METRICS or "loss" in metric

        if is_loss:
            outcome = "regression" if raw_direction == "rise" else "improvement"
        else:
            outcome = "improvement" if raw_direction == "rise" else "regression"


        return {
            "metric": metric,
            "direction": raw_direction,
            "outcome": outcome,
            "avg": round(avg, 4),
            "current": round(current, 4),
            "delta": round(delta, 4),
        }