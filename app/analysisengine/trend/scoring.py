from typing import List

TREND_DROP_PENALTY = 0.05

class TrendScoring:
    @staticmethod
    def calculate_penalty(dropped_metrics: List[str]) -> float:
        return len(dropped_metrics) * TREND_DROP_PENALTY