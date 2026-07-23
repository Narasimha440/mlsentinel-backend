""""
Health score of mlsentinal v0.1.0

gives overall score of the model
"""

from typing import Dict, List
from .severity import Severity
from .rule_engine import Rule

SEVERITY_PRIORITY = {Severity.CRITICAL: 0.15, Severity.WARNING: 0.07, Severity.INFO: 0.02}

class HealthScore:

    @staticmethod
    def calculate(metrics: Dict[str, float], matched_rules: List[Rule]) -> float:
        base = (metrics.get("accuracy", 0) * 0.3 + metrics.get("precision", 0) * 0.2 + metrics.get("recall", 0) * 0.2 + metrics.get("f1_score", 0) * 0.2 + max(0, 1 - metrics.get("val_loss", 0)) * 0.1)
        for rule in matched_rules:
            base -= SEVERITY_PRIORITY.get(rule.severity, 0)

        return round(max(0.0, min(base, 1.0)) * 100, 2)