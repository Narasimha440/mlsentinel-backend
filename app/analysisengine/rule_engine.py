from typing import Dict, List, Any
from .rules import RULES
from .models import Rule
from .severity import Severity
from .drift import DriftDetector

SEVERITY_ORDER = {Severity.CRITICAL: 0, Severity.WARNING: 1, Severity.INFO: 2}

class RuleEngine:

    @staticmethod
    def evaluate(metrics: Dict[str, float]) -> List[Rule]:
        matched = [rule for rule in RULES if rule.condition.evaluate(metrics)]
        return sorted(matched, key=lambda r: SEVERITY_ORDER.get(r.severity, 99))

    @staticmethod
    def evaluate_drift(feature_payloads: Dict[str, Dict[str, list]]) -> List[Dict[str, Any]]:
        drift_alerts = []


        for feature_name, data in feature_payloads.items():
            baseline = data.get("baseline", [])
            current = data.get("current", [])

            if not baseline or not current:
                continue

            analysis = DriftDetector.analyze_feature_drift(
                feature_name,
                baseline,
                current,
                is_categorical=False
            )

            if analysis["drift_detected"]:
                severity_str = analysis.get("severity", "warning")


                drift_alerts.append({
                    "type": "data_drift",
                    "feature": feature_name,
                    "severity": severity_str,
                    "message": f"Significant data drift detected in feature '{feature_name}'. PSI Score: {analysis['metrics']['psi']:.3f}.",
                    "metrics": analysis["metrics"]
                })

        return drift_alerts