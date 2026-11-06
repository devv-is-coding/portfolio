from app.worker import celery_app


@celery_app.task(name="system.ping")
def ping() -> str:
    """Round-trip check for the worker: `ping.delay().get(timeout=10) == "pong"`."""
    return "pong"
