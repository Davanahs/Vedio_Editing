"""
Async Background Tasks for Reel Editor Queue.
"""
from typing import Dict, Any
from engine.task_queue.worker import app

if app:
    @app.task(name="tasks.process_video")
    def process_video_task(video_path: str, output_path: str, preview: bool = False) -> Dict[str, Any]:
        """
        Background task to process a video end-to-end.
        """
        import asyncio
        from engine.pipeline import run_pipeline
        return asyncio.run(run_pipeline(video_path=video_path, output_path=output_path, preview=preview))
else:
    def process_video_task(*args, **kwargs):
        raise RuntimeError("Celery is not installed or configured.")
