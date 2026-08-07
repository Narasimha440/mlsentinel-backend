from dataclasses import dataclass
from typing import Dict, Any, List
from .severity import Severity

@dataclass
class DataQualityFinding:
    column: str
    issue: str
    severity: Severity
    detail: str


class DataQualityThresholds:
    null_warning_pct = 5.0
    null_critical_pct = 20.0
    duplicate_warning_pct = 5.0
    duplicate_critical_pct = 15.0
    outlier_warning_pct = 5.0
    top_value_dominance_pct = 0.95


class DataQualityEngine:

    @staticmethod
    def evaluate(summary: Dict[str, Any]) -> List[DataQualityFinding]:
        findings = []
        t = DataQualityThresholds

        dup_pct = summary.get("duplicate_row_percentage", 0)
        if dup_pct >= t.duplicate_critical_pct:
            findings.append(DataQualityFinding("(all rows)", "high_duplicates", Severity.CRITICAL,
                f"{dup_pct}% of rows are exact duplicates."))
        elif dup_pct >= t.duplicate_warning_pct:
            findings.append(DataQualityFinding("(all rows)", "moderate_duplicates", Severity.WARNING,
                f"{dup_pct}% of rows are exact duplicates."))

        for col_name, col_info in summary.get("columns", {}).items():
            null_pct = col_info.get("null_percentage", 0)
            if null_pct >= t.null_critical_pct:
                findings.append(DataQualityFinding(col_name, "high_missing_values", Severity.CRITICAL,
                    f"{null_pct}% of values are missing."))
            elif null_pct >= t.null_warning_pct:
                findings.append(DataQualityFinding(col_name, "moderate_missing_values", Severity.WARNING,
                    f"{null_pct}% of values are missing."))

            outlier_pct = col_info.get("outlier_percentage")
            if outlier_pct is not None and outlier_pct >= t.outlier_warning_pct:
                findings.append(DataQualityFinding(col_name, "outlier_detected", Severity.WARNING,
                    f"{outlier_pct}% of values are statistical outlier (IQR method)."))

            top_ratio = col_info.get("top_value_ratio")
            if top_ratio is not None and top_ratio >= t.top_value_dominance_pct:
                findings.append(DataQualityFinding(col_name, "low_variance", Severity.WARNING,
                    f"One value makes up {round(top_ratio * 100, 1)}% of this column - may be uninformative."))

        return findings