from typing import Dict
from .storage import RunHistoryStorage

class TrendTracker:
    def __init__(self, storage: RunHistoryStorage, project: str, model: str, window: int = 10):
        self.storage = storage
        self.project = project
        self.model = model
        self.window = window

    def detect_drop(self, metric: str, drop_threshold: float = 0.10) -> bool:
        history = self.storage.get_recent(self.project, self.model, self.window)
        if len(history) < 3:
            return False

        recent = [m.get(metric, 0) for m in history[:-1]]
        avg = sum(recent) / len(recent)
        current = history[-1].get(metric, 0)
        return (avg - current) > drop_threshold