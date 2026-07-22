from typing import Dict, List
from .rules import RULES
from .models import Rule
from .severity import Severity

SEVERITY_ORDER = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}

class RuleEngine:

    @staticmethod
    def evaluate(metrics: Dict[str, float]) -> List[Rule]:
        matched = [rule for rule in RULES if rule.condition.evaluate(metrics)]
        return sorted(matched, key=lambda r: SEVERITY_ORDER.get(r.severity, 99))