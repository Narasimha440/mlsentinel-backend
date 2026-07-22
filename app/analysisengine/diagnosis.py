from typing import Dict
from .rule_engine import RuleEngine

class Diagnosis:

    @staticmethod
    def analyze(metrics: Dict[str, float]) -> list[str]:
        matched_rules = RuleEngine.evaluate(metrics)

        if not matched_rules:
            return ["Model performance appears healthy."]

        return [
            rule.diagnosis
            for rule in matched_rules
        ]