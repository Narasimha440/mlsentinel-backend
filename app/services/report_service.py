from sqlalchemy.orm import Session

from app.models.report import ReportRequest
from app.analysisengine.analysis_engine import AnalysisEngine
from app.analysisengine.trend.storage import RunHistoryStorage
from app.analysisengine.trend.tracker import TrendTracker
from app.analysisengine.trend.scoring import TrendScoring
from app.services.hierarchy_service import HierarchyService


class ReportService:

    @staticmethod
    def process_method(report: ReportRequest, db: Session, owner_uid: str):

        ml_model_id = HierarchyService.resolve_model_id(db, owner_uid, report.project, report.model)

        result = AnalysisEngine.run(report.metrics)

        storage = RunHistoryStorage(db)
        storage.save(
            ml_model_id=ml_model_id,
            metrics=report.metrics,
            health_score=result.health_score,
        )

        tracker = TrendTracker(storage=storage, ml_model_id=ml_model_id)
        dropped_metrics = [
            metric
            for metric in ["accuracy", "precision", "recall", "f1_score"]
            if metric in report.metrics and tracker.detect_drop(metric)
        ]

        trend_findings = [
            f"{metric} dropped compared to recent average - possible regressions."
            for metric in dropped_metrics
        ] or ["No significant trend issues detected."]

        penalty = TrendScoring.calculate_penalty(dropped_metrics)
        adjusted_health_score = round(max(0.0, result.health_score - (penalty * 100)), 2)

        response = {
            "success": True,
            "message": "Report processed successfully!",
            "project": report.project,
            "model": report.model,
            "health_score": adjusted_health_score,
            "diagnosis": result.diagnoses,
            "recommendation": result.recommendation,
            "trend_findings": trend_findings,
            "metrics": report.metrics
        }

        return response