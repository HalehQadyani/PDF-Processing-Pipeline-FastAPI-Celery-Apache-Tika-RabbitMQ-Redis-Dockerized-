import os
from celery import Celery

BROKER_URL = os.environ.get("RABBITMQ_BROKER_URL", "amqp://guest:guest@rabbitmq:5672//")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery("pdf_tasks", broker=BROKER_URL, backend=RESULT_BACKEND)

celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_time_limit=600,     
    task_soft_time_limit=540,
)

celery_app.autodiscover_tasks(["app.tasks"])