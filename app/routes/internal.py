from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os

from app.db.session import get_db
from app.models.schedule_settings import ScheduleFrequency, ScheduleSettings
from app.models.alert import Alert
from app.analysisengine.trend.tracker import TrendTracker
from app.analysisengine.trend.storage import RunHistoryStorage

router = APIRouter()

load_dotenv()

INTERNAL_SECRET = os.getenv("INTERNAL_CRON_SECRET")

FREQUENCY_DELTA = {
    ScheduleFrequency.DAILY: timedelta(days=1),
    ScheduleFrequency.WEEKLY: timedelta(weeks=1),
    ScheduleFrequency.MONTHLY: timedelta(days=30),
}


METRICS_TO_CHECK = ["accuracy", "precision", "recall", "f1_score"]


@router.post("/internal/run-due-schedules")
def run_due_schedule(db: Session = Depends(get_db), x_internal_secret: str = Header(None)):

    if x_internal_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")

    now = datetime.now(timezone.utc)
    storage = RunHistoryStorage(db)

    schedules = db.query(ScheduleSettings).filter(ScheduleSettings.frequency != ScheduleFrequency.OFF).all()


    checked_count = 0
    alerts_created = 0

    for sched in schedules:
        delta = FREQUENCY_DELTA[sched.frequency]

        is_due = sched.last_run_at is None or (now - sched.last_run_at) >= delta
        if not is_due:
            continue

        checked_count += 1

        tracker = TrendTracker(storage=storage, ml_model_id=sched.ml_model_id)

        for metric in METRICS_TO_CHECK:

            if tracker.detect_drop(metric):
                alert = Alert(
                    ml_model_id = sched.ml_model_id,
                    severity = "warning",
                    message = f"{metric} dropped compared to recent average - possible regression.",
                )
                db.add(alert)
                alerts_created += 1

        sched.last_run_at = now

    db.commit()

    return {
        "checked": checked_count,
        "alerts_created": alerts_created,
        "ran_at": now.isoformat(),
    }