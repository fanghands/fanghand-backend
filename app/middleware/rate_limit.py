import time

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

from app.config import settings

# Default: 60 requests per minute
DEFAULT_RATE_LIMIT = 60
DEFAULT_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based GCRA rate limiter per IP address.

    Gracefully skips rate limiting if Redis is unavailable.
    """

    def __init__(self, app, rate_limit: int = DEFAULT_RATE_LIMIT, window: int = DEFAULT_WINDOW_SECONDS):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window = window
        self._redis = None
        self._redis_failed = False

    async def _get_redis(self):
        if self._redis_failed or aioredis is None:
            return None
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=2,
                )
                await self._redis.ping()
            except Exception as exc:
                logger.warning("Redis unavailable for rate limiting: {}", str(exc))
                self._redis = None
                self._redis_failed = True
                return None
        return self._redis

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        redis_client = await self._get_redis()

        if redis_client is not None:
            key = f"rl:{client_ip}"
            try:
                # Simple sliding-window counter using Redis
                now = time.time()
                pipe = redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, now - self.window)
                pipe.zadd(key, {str(now): now})
                pipe.zcard(key)
                pipe.expire(key, self.window)
                results = await pipe.execute()
                request_count = results[2]

                if request_count > self.rate_limit:
                    logger.info("Rate limit exceeded for IP {}", client_ip)
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded. Try again later."},
                        headers={"Retry-After": str(self.window)},
                    )
            except Exception as exc:
                logger.warning("Rate limit check failed: {}", str(exc))
                # Fail open — allow the request

        return await call_next(request)
