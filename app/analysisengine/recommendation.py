from typing import Dict, List
from .rule_engine import RuleEngine
from .models import Rule

class Recommendation:

    @staticmethod
    def generate(metrics: Dict[str, float]) -> List[str]:
        matched_rules = RuleEngine.evaluate(metrics)
        if not matched_rules:
            return ["No major improvements required.!!"]
        return [rule.recommendation for rule in matched_rules]