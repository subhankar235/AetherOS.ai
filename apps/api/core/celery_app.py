from celery import Celery
from celery.schedules import crontab
from core.config import settings

celery_app = Celery(
    "aetheros_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "refresh-research-cache-every-6-hours": {
            "task": "workers.research_cache_refresh.refresh_research_cache",
            "schedule": crontab(hour="*/6"),
            "options": {"queue": "periodic"},
        },
    },
)
