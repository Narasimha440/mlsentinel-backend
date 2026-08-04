from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

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
    model_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: dict = Depends(verify_firebase_token),
):
    """
    Returns everything the dashboard needs in one call.
    If model_id is provided, every section is scoped to just that model.
    If model_id is omitted, everything is aggregated across all of the
    user's models (the default "overview" behavior).
    """
    owner_uid = user["uid"]

    # Step 1 — find this user's workspace. If they don't have one yet
    # (brand new account), return an empty-but-valid shape so the
    # frontend doesn't crash on missing fields.
    workspace = db.query(Workspace).filter(Workspace.owner_firebase_uid == owner_uid).first()
    if not workspace:
        return {
            "summary": {"overall_health_score": None, "active_models": 0, "healthy_models": 0, "critical_models": 0},
            "health_trend": [],
            "model_performance": [],
            "findings": [],
            "recommendations": [],
            "recent_reports": [],
            "available_models": [],
        }

    # Step 2 — get every project this workspace owns, then every model
    # under those projects. This is the user's FULL model list, always,
    # regardless of whether they filtered to one specific model below.
    project_ids = [p.id for p in db.query(Project).filter(Project.workspace_id == workspace.id).all()]
    all_models = db.query(MLModel).filter(MLModel.project_id.in_(project_ids)).all() if project_ids else []

    # Build a lookup from project_id -> Project, so we can show project
    # names alongside model names later without extra queries in a loop.
    project_by_id = {p.id: p for p in db.query(Project).filter(Project.id.in_(project_ids)).all()} if project_ids else {}

    # Step 3 — decide which models to actually analyze in this response.
    # If the user picked a specific model_id, narrow down to just that one.
    # We only keep it if it's actually in all_models — this means a user
    # can never request another user's model_id and get data back, since
    # all_models is already scoped to their own workspace.
    if model_id is not None:
        models = [m for m in all_models if m.id == model_id]
    else:
        models = all_models

    model_ids = [m.id for m in models]

    # Step 4 — for each model being analyzed, find its latest run,
    # re-run the rule engine on it, and classify its status.
    model_performance = []
    all_findings = []
    all_recommendations = []
    healthy_count = warning_count = critical_count = 0
    health_scores = []

    for model in models:
        latest_run = (
            db.query(RunHistory)
            .filter(RunHistory.ml_model_id == model.id)
            .order_by(RunHistory.created_at.desc())
            .first()
        )

        if not latest_run:
            # this model has never had a report submitted — skip it,
            # nothing to show in performance/findings for it yet
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

        project = project_by_id.get(model.project_id)
        project_name = project.name if project else None

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

    # Step 5 — health score trend, averaged per day, across only the
    # models we're currently analyzing (all of them, or just the one
    # selected — model_ids already reflects that).
    cutoff = datetime.utcnow() - timedelta(days=days)

    from sqlalchemy import func
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

    # Step 6 — the 10 most recent individual runs, across the models
    # we're analyzing, newest first.
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
            "project": project_by_id.get(model.project_id).name if model and model.project_id in project_by_id else None,
            "model": model.name if model else None,
            "health_score": run.health_score,
            "issues": len(matched),
            "timestamp": run.created_at.isoformat(),
        })

    overall_health_score = round(sum(health_scores) / len(health_scores), 2) if health_scores else None

    # Step 7 — return everything. Note that "available_models" always
    # lists ALL of the user's models (from all_models, not the filtered
    # `models`), so the frontend dropdown always has every option to
    # choose from, no matter which one is currently selected.
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
        "available_models": [
            {
                "model_id": m.id,
                "name": m.name,
                "project": project_by_id.get(m.project_id).name if m.project_id in project_by_id else None,
            }
            for m in all_models
        ],
    }