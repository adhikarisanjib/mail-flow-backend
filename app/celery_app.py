import logging

from celery import Celery
from celery.signals import task_postrun, task_prerun

from app.settings import settings

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "email_service",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # Results expire after 1 hour
)


@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **kw):
    """Handle task start"""
    logger.info(f"Task {task.name} started: {task_id}")


@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, state, **kw):
    """Handle task completion"""
    logger.info(f"Task {task.name} completed: {task_id}")
