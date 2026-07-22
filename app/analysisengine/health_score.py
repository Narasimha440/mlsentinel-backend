""""
Health score of mlsentinal v0.1.0

gives overall score of the model
"""

from typing import Dict

class HealthScore:

    @staticmethod
    def calculate(metrics: Dict[str, float]) -> float:

        #getting the metrics from the json
        accuracy = metrics.get("accuracy", 0)
        precision = metrics.get("precision", 0)
        recall = metrics.get("recall", 0)
        f1_score = metrics.get("f1_score", 0)
        val_loss = metrics.get("val_loss", 0)

        #calculating the score
        score = (accuracy + precision + recall + f1_score) / 4

        #if validation loss was high score will be decreased
        if (val_loss > 0.5):
            score -= 0.10

        #making score range from 0 to 1
        score = max(0.0, min(score, 1.0))

        #rounding and converting 0.94 to 94.0
        return round(score*100, 2)