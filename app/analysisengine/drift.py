import numpy as np
from scipy import stats
from typing import List, Dict, Any, Union
from .thresholds import Thresholds

class DriftDetector:

    @staticmethod
    def calculate_psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
        if len(expected) == 0 or len(actual) == 0:
            return 0.0

        breakpoints = np.arange(0, buckets + 1) / (buckets) * 100
        bins = np.percentile(expected, breakpoints)

        bins[0] = bins[0] - 0.0001
        bins[-1] = bins[-1] + 0.0001

        expected_counts, _ = np.histogram(expected, bins=bins)
        actual_counts, _ = np.histogram(actual, bins=bins)


        expected_percents = expected_counts / len(expected)
        actual_percents = actual_counts / len(actual)

        epsilon = 0.0001
        expected_percents = np.where(expected_percents == 0, epsilon, expected_percents)
        actual_percents = np.where(actual_percents == 0, epsilon, actual_percents)

        psi_values = (actual_percents - expected_percents) * np.log(actual_percents / expected_percents)


        return float(np.sum(psi_values))

    @staticmethod
    def calculate_ks_statistic(expected: np.ndarray, actual: np.ndarray) -> Dict[str, float]:
        if len(expected) == 0 or len(actual) == 0:
            return {"statistic": 0.0, "p_value": 1.0}

        ks_stat, p_value = stats.ks_2samp(expected, actual)

        return {
            "statistic": float(ks_stat),
            "p_value": float(p_value)
        }

    @classmethod
    def analyze_feature_drift(cls, feature_name: str, baseline_data: list, current_data: list, is_categorical: bool = False) -> Dict[str, Any]:
        expected = np.array(baseline_data)
        actual = np.array(current_data)


        results = {
            "feature": feature_name,
            "drift_detected": False,
            "metrics": {}
        }

        if is_categorical:
            pass
        else:
            psi_score = cls.calculate_psi(expected, actual)
            ks_results = cls.calculate_ks_statistic(expected, actual)

            results["metrics"] = {
                "psi": psi_score,
                "ks_statistic": ks_results["statistic"],
                "ks_p_value": ks_results["p_value"]
            }

            t = Thresholds.DRIFT_THRESHOLDS["psi"]

            if psi_score >= t["warning"] or (ks_results["p_value"] < 0.05 and ks_results["statistic"] > 0.1):
                results["drift_detected"] = True
                results["severity"] = "critical" if psi_score >= t["critical"] else "warning"

        return results