from dataclasses import dataclass
from typing import Dict, List
from .rule_engine import RuleEngine
from .health_score import HealthScore
from .models import Rule

@dataclass
class DiagnosisReport:
    health_score: float
    diagnoses: List[str]
    recommendation: List[str]
    matched_rules: List[Rule]

class AnalysisEngine:
    @staticmethod
    def run(metrics: Dict[str, float]) -> DiagnosisReport:
        matched = RuleEngine.evaluate(metrics)
        return DiagnosisReport(
            health_score=HealthScore.calculate(metrics, matched),
            diagnoses=[r.diagnosis for r in matched] or ["Model performance appears healthy."],
            recommendation=[r.recommendation for r in matched] or ["No major improvements required."],
            matched_rules=matched,
        )