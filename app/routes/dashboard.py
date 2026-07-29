from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.ml_model import MLModel
from app.models.run_history import RunHistory
from app.auth.firebase import verify_firebase_token
from app.analysisengine.rule_engine import RuleEngine
from app.analysisengine.severity import Severity

router = APIRouter()


def _model_status(matched_rules) -> str:
    severities = {r.severity for r in matched_rules}
    if Severity.CRITICAL in severities:
        return "Critical"
    if Severity.WARNING in severities:
        return "Warning"
    return "Healthy"


@router.get("/dashboard")
def get_dashboard(
    days: int = Query(7, le=90),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token),
):
    """
    Single aggregated payload for the dashboard's main view:
    summary counts, health score trend, model performance table,
    live findings/recommendations (recomputed from latest metrics),
    and recent run history.
    """
    owner_uid = user["uid"]

    workspace = db.query(Workspace).filter(Workspace.owner_firebase_uid == owner_uid).first()
    if not workspace:
        return {
            "summary": {"overall_health_score": None, "active_models": 0, "healthy_models": 0, "critical_models": 0},
            "health_trend": [],
            "model_performance": [],
            "findings": [],
            "recommendations": [],
            "recent_reports": [],
        }

    project_ids = [p.id for p in db.query(Project).filter(Project.workspace_id == workspace.id).all()]
    models = db.query(MLModel).filter(MLModel.project_id.in_(project_ids)).all() if project_ids else []
    model_ids = [m.id for m in models]

    model_performance = []
    all_findings = []
    all_recommendations = []
    healthy_count = warning_count = critical_count = 0
    health_scores = []

    project_by_id = {p.id: p for p in db.query(Project).filter(Project.id.in_(project_ids)).all()} if project_ids else {}

    for model in models:
        latest_run = (
            db.query(RunHistory)
            .filter(RunHistory.ml_model_id == model.id)
            .order_by(RunHistory.created_at.desc())
            .first()
        )

        if not latest_run:
            continue

        matched_rules = RuleEngine.evaluate(latest_run.metrics)
        status = _model_status(matched_rules)

        if status == "Healthy":
            healthy_count += 1
        elif status == "Warning":
            warning_count += 1
        else:
            critical_count += 1

        if latest_run.health_score is not None:
            health_scores.append(latest_run.health_score)

        project_name = project_by_id.get(model.project_id).name if model.project_id in project_by_id else None

        model_performance.append({
            "model_id": model.id,
            "project": project_name,
            "name": model.name,
            "health_score": latest_run.health_score,
            "metrics": latest_run.metrics,
            "status": status,
            "last_updated": latest_run.created_at.isoformat(),
        })

        for rule in matched_rules:
            all_findings.append({
                "model": model.name,
                "issue": rule.diagnosis,
                "severity": rule.severity.value,
                "detected_at": latest_run.created_at.isoformat(),
            })
            all_recommendations.append({
                "model": model.name,
                "recommendation": rule.recommendation,
                "severity": rule.severity.value,
            })


    cutoff = datetime.utcnow() - timedelta(days=days)
    trend_rows = (
        db.query(
            func.date(RunHistory.created_at).label("day"),
            func.avg(RunHistory.health_score).label("avg_score"),
        )
        .filter(RunHistory.ml_model_id.in_(model_ids), RunHistory.created_at >= cutoff)
        .group_by(func.date(RunHistory.created_at))
        .order_by(func.date(RunHistory.created_at))
        .all()
    ) if model_ids else []

    health_trend = [{"date": str(row.day), "health_score": round(row.avg_score, 2)} for row in trend_rows]


    recent_runs = (
        db.query(RunHistory)
        .filter(RunHistory.ml_model_id.in_(model_ids))
        .order_by(RunHistory.created_at.desc())
        .limit(10)
        .all()
    ) if model_ids else []

    model_lookup = {m.id: m for m in models}
    recent_reports = []
    for run in recent_runs:
        model = model_lookup.get(run.ml_model_id)
        matched = RuleEngine.evaluate(run.metrics)
        recent_reports.append({
            "project": project_by_id.get(model.project_id).name if model else None,
            "model": model.name if model else None,
            "health_score": run.health_score,
            "issues": len(matched),
            "timestamp": run.created_at.isoformat(),
        })

    overall_health_score = round(sum(health_scores) / len(health_scores), 2) if health_scores else None

    return {
        "summary": {
            "overall_health_score": overall_health_score,
            "active_models": len(models),
            "healthy_models": healthy_count,
            "warning_models": warning_count,
            "critical_models": critical_count,
        },
        "health_trend": health_trend,
        "model_performance": model_performance,
        "findings": sorted(all_findings, key=lambda f: f["severity"] != "critical"),
        "recommendations": all_recommendations,
        "recent_reports": recent_reports,
    }