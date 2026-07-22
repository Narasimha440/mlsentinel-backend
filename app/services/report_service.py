from app.models.report import ReportRequest

from app.analysisengine.health_score import HealthScore
from app.analysisengine.diagnosis import Diagnosis
from app.analysisengine.recommendation import Recommendation


class ReportService:

    @staticmethod
    def process_method(report: ReportRequest):

        health_score = HealthScore.calculate(report.metrics)

        diagnosis = Diagnosis.analyze(report.metrics)

        recommendation = Recommendation.generate(report.metrics)

        response = {
            "success": True,
            "message": "Report processed successfully!",
            "project": report.project,
            "model": report.model,
            "health_score": health_score,
            "diagnosis": diagnosis,
            "recommendation": recommendation,
            "metrics": report.metrics
        }

        return response