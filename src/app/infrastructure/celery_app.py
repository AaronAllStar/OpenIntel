from celery import Celery

from src.app.infrastructure.config import get_settings

settings = get_settings()

celery_app = Celery(
    "openintel",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.app.application.worker_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_soft_time_limit=300,
    task_time_limit=360,
    worker_prefetch_multiplier=1,
    broker_connection_timeout=1.0,
    broker_connection_retry_on_startup=False,
    task_always_eager=(settings.ENV == "test"),
)
