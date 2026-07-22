from .models import Rule
from .conditions import LessThan, GreaterThan, GapExceeds
from .thresholds import Thresholds
from .severity import Severity

T = Thresholds()

RULES = [
    Rule("low_accuracy", Severity.CRITICAL, "performance",
         LessThan("accuracy", T.accuracy_min),
         "Model accuracy is too low.",
         "Collect more training data or retrain with a better model."),

    Rule("low_precision", Severity.WARNING, "performance",
         LessThan("precision", T.precision_min),
         "Model produces many false positives.",
         "Tune the classification threshold or improve feature engineering."),

    Rule("low_recall", Severity.WARNING, "performance",
         LessThan("recall", T.recall_min),
         "Model misses many positive samples.",
         "Increase recall through threshold tuning or rebalance the dataset."),

    Rule("high_validation_loss", Severity.WARNING, "generalization",
         GreaterThan("val_loss", T.val_loss_max),
         "High validation loss detected.",
         "Consider regularization or early stopping."),

    Rule("overfitting", Severity.CRITICAL, "generalization",
         GapExceeds("train_accuracy", "accuracy", T.overfit_gap_max),
         "Large gap between train and validation accuracy suggests overfitting.",
         "Add regularization, reduce model complexity, or get more training data."),

    Rule("precision_recall_imbalance", Severity.INFO, "performance",
         GapExceeds("precision", "recall", 0.25),
         "Precision and recall are significantly imbalanced.",
         "Review whether your decision threshold matchs the cot of false positives vs false negatives."),
]