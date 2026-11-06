import sentry_sdk

from app.core.config import Settings


def init_sentry(settings: Settings) -> None:
    """Enable Sentry (FastAPI + Celery integrations load automatically) when SENTRY_DSN is set."""
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
    )
