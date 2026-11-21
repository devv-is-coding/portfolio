"""Background work run by the API process itself (TASK_RUNNER=api), for hosts without a
Celery worker. Routers hand it to FastAPI's BackgroundTasks, so it runs right after the
response is sent, inside the same request: the visitor never waits for it, and a host
that scales to zero keeps the process alive until it's done."""

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence

logger = logging.getLogger(__name__)

# Seconds to wait before each retry: three attempts in all. Short, unlike the worker's
# backoff, because the request stays open until the work is done.
RETRY_DELAYS: tuple[float, ...] = (1.0, 4.0)


async def run_with_retries(
    work: Callable[[], Awaitable[None]],
    *,
    retry_on: tuple[type[Exception], ...],
    description: str,
    delays: Sequence[float] | None = None,
) -> None:
    """Run `work`, retrying on `retry_on` errors (waiting RETRY_DELAYS unless `delays` is
    given). Never raises: the response is already sent, so a failure can only be logged."""
    delays = RETRY_DELAYS if delays is None else delays
    for attempt in range(1, len(delays) + 2):
        try:
            await work()
        except retry_on:
            if attempt > len(delays):
                logger.exception("%s failed after %d attempts", description, attempt)
                return
            delay = delays[attempt - 1]
            logger.warning("%s failed (attempt %d), retrying in %s s", description, attempt, delay)
            await asyncio.sleep(delay)
        except Exception:
            logger.exception("%s failed", description)
            return
        else:
            return
