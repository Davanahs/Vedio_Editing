"""
Celery Worker Configuration for Reel Editor.
"""
import os

try:
    from celery import Celery
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    app = Celery("reel_engine", broker=redis_url, backend=redis_url)
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
    )
except ImportError:
    app = None
