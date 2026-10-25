from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

celery_app = Celery("enterprise", broker=get_settings().redis_url, backend=get_settings().redis_url)
celery_app.conf.update(
    task_serializer="json", result_serializer="json", accept_content=["json"], timezone="UTC",
    beat_schedule={"daily-empty-report": {"task": "app.workers.tasks.daily_report", "schedule": crontab(hour=6, minute=0)}},
)
