import asyncio
import logging
from datetime import datetime, timezone, timedelta

from core.celery_app import celery_app
from core.config import settings

logger = logging.getLogger("workers.research_cache_refresh")

CACHE_TTL_HOURS = 24


async def _refresh_cache() -> int:
    from qdrant_client.http import models as qdrant_models
    from integrations.qdrant_client import qdrant_client

    cutoff = datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)
    cutoff_str = cutoff.isoformat()

    client = qdrant_client.get_client()

    stale_filter = qdrant_models.Filter(
        must=[
            qdrant_models.FieldCondition(
                key="cached_at",
                range=qdrant_models.Range(
                    lt=cutoff_str,
                ),
            ),
        ],
    )

    result = await client.delete(
        collection_name=settings.QDRANT_COLLECTION_RESEARCH_CACHE,
        points_selector=qdrant_models.FilterSelector(
            filter=stale_filter,
        ),
    )

    deleted_count = getattr(result, "count", 0)
    logger.info(f"Research cache refresh: deleted {deleted_count} stale entries (TTL: {CACHE_TTL_HOURS}h)")
    return deleted_count


@celery_app.task(name="workers.research_cache_refresh.refresh_research_cache")
def refresh_research_cache() -> int:
    logger.info("Starting periodic research cache refresh...")
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    coro = _refresh_cache()

    if loop and loop.is_running():
        import threading
        import queue

        q = queue.Queue()

        def run_in_thread():
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                res = new_loop.run_until_complete(coro)
                q.put((True, res))
            except Exception as e:
                q.put((False, e))
            finally:
                new_loop.close()

        t = threading.Thread(target=run_in_thread)
        t.start()
        t.join()

        success, val = q.get()
        if not success:
            raise val
        return val
    else:
        return asyncio.run(coro)
