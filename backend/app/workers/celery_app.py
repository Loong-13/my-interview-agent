from celery import Celery

from backend.app.core.config import settings

celery_app = Celery(
    "pyoffer_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.tasks.resume_tasks",
        "app.workers.tasks.jd_tasks",
        "app.workers.tasks.match_tasks",
        "app.workers.tasks.question_tasks",
        "app.workers.tasks.interview_tasks",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    timezone="UTC",
)

