import os

from celery import Celery

from engine.analyzer import run_analysis
from engine.logger import logger

# Initialize Celery
# internal_url uses 'redis' hostname from docker-compose
# local fallback uses localhost
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "comms_forensics",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(bind=True)
def analyze_case_task(self, config_path: str):
    """
    Celery task to run the analysis in the background.
    """
    logger.info("async_analysis_started", task_id=self.request.id, config=config_path)
    try:
        run_analysis(config_path)
        logger.info("async_analysis_completed", task_id=self.request.id)
        return {"status": "completed", "config": config_path}
    except Exception as e:
        logger.error("async_analysis_failed", task_id=self.request.id, error=str(e))
        # Re-raise so Celery marks it as failed
        raise e
