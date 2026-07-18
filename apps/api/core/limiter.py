import time
import logging
import redis.asyncio as aioredis
from core.config import settings
from core.exceptions import RateLimitError

logger = logging.getLogger("core.limiter")


class RedisRateLimiter:
    """
    Sliding window log rate limiter using Redis sorted sets.
    """
    def __init__(self) -> None:
        self.redis = aioredis.from_url(settings.REDIS_URL)

    async def check_rate_limit(self, key: str, limit: int, period: int = 60) -> None:
        """
        Check rate limit against a Redis sorted set.
        Raises RateLimitError if limit exceeded.
        """
        now = time.time()
        clear_before = now - period
        
        # Use key prefix
        redis_key = f"rate_limit:{key}"
        
        try:
            pipe = self.redis.pipeline()
            # Remove timestamps outside the sliding window
            pipe.zremrangebyscore(redis_key, 0, clear_before)
            # Count remaining timestamps in window
            pipe.zcard(redis_key)
            # Add current timestamp
            pipe.zadd(redis_key, {str(now): now})
            # Expire key to clean up space
            pipe.expire(redis_key, period)
            
            _, count, _, _ = await pipe.execute()
            
            if count >= limit:
                logger.warning(f"Rate limit hit for '{key}' - current count is {count}, limit is {limit} per {period}s")
                raise RateLimitError(f"Rate limit exceeded for {key.split(':')[0]}. Limit is {limit} per {period} seconds.")
        except RateLimitError as exc:
            raise exc
        except Exception as exc:
            # Degrade gracefully by logging the redis error but allowing the request to proceed in dev
            logger.error(f"Redis rate limiter exception (graceful degradation): {exc}")


# Global instance
limiter = RedisRateLimiter()
