from sqlalchemy.orm import Session

from app.models.report import ReportRequest
from app.analysisengine.analysis_engine import AnalysisEngine
from app.analysisengine.trend.storage import RunHistoryStorage
from app.analysisengine.trend.tracker import TrendTracker


class ReportService:

    @staticmethod
    def process_method(report: ReportRequest, db: Session):

        result = AnalysisEngine.run(report.metrics)

        storage = RunHistoryStorage(db)
        storage.save(
            project=report.project,
            model=report.model,
            metrics=report.metrics,
            health_score=result.health_score,
        )

        tracker = TrendTracker(storage=storage, project=report.project, model=report.model)
        trend_findings = [
            f"{metric} dropped accuracy to recent average - possible regressions."
            for metric in ["accuracy", "precisio", "recall", "f1_score"]
            if metric in report.metrics and tracker.detect_drop(metric)
        ]

        response = {
            "success": True,
            "message": "Report processed successfully!",
            "project": report.project,
            "model": report.model,
            "health_score": result.health_score,
            "diagnosis": result.diagnoses,
            "recommendation": result.recommendation,
            "trend_findings": trend_findings or ["No significant trend issues detected."],
            "metrics": report.metrics
        }

        return response