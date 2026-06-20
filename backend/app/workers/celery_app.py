"""后台任务使用的 Celery 应用配置。"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "pyoffer_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        # 导入任务模块，确保 Celery 启动时能发现已注册任务。
        "app.workers.tasks.resume_tasks",
        "app.workers.tasks.jd_tasks",
        "app.workers.tasks.match_tasks",
        "app.workers.tasks.question_tasks",
        "app.workers.tasks.interview_tasks",
        "app.workers.tasks.knowledge_tasks",
    ],
)

celery_app.conf.update(
    # 跟踪任务进度并设置超时，避免任务永久卡住。
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    timezone="UTC",
)
