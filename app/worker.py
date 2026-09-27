"""
Celery worker process
Run with: celery -A app.celery_app worker --loglevel=info --concurrency=4
"""

import logging

from app import tasks
from app.celery_app import celery_app

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Celery worker...")
    celery_app.start()
