from dataclasses import dataclass

@dataclass(frozen=True)
class Thresholds:
    accuracy_min: float = 0.60
    precision_min: float = 0.60
    recall_min: float = 0.60
    val_loss_max: float = 0.50
    overfit_gap_max: float = 0.15