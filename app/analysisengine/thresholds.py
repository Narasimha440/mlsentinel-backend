from dataclasses import dataclass

@dataclass(frozen=True)
class Thresholds:
    accuracy_min: float = 0.60
    precision_min: float = 0.60
    recall_min: float = 0.60
    val_loss_max: float = 0.50
    overfit_gap_max: float = 0.15

    # Add these new thresholds to your existing configuration

    DRIFT_THRESHOLDS = {
        "psi": {
            "warning": 0.1,   # > 0.1 means slight drift
            "critical": 0.2   # > 0.2 means significant drift requiring retraining
        },
        "ks_statistic": {
            "warning": 0.1,
            "critical": 0.2 
        },
        "ks_p_value": {
            "critical": 0.05  # < 0.05 means distributions are statistically different
        }
    }