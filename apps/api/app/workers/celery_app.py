from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "betlens",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.tasks.ingestion",
        "app.workers.tasks.predictions",
        "app.workers.tasks.notifications",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ── Scheduled tasks (Celery Beat) ─────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "sync-reference-data": {
        "task": "app.workers.tasks.ingestion.sync_reference_data",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3am UTC
    },
    "sync-fixtures": {
        "task": "app.workers.tasks.ingestion.sync_fixtures",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
    "sync-standings": {
        "task": "app.workers.tasks.ingestion.sync_standings_and_stats",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
    "sync-injuries": {
        "task": "app.workers.tasks.ingestion.sync_injuries",
        "schedule": crontab(minute=0, hour="*/2"),  # Every 2 hours
    },
    "sync-odds": {
        "task": "app.workers.tasks.ingestion.sync_odds",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
    "run-predictions": {
        "task": "app.workers.tasks.predictions.run_predictions",
        "schedule": crontab(hour=2, minute=0),  # Nightly at 2am UTC
    },
    "send-notifications": {
        "task": "app.workers.tasks.notifications.send_queued_notifications",
        "schedule": crontab(minute="*/1"),  # Every minute
    },
}