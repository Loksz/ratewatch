import time

import redis.asyncio as aioredis

from ratewatch.models.config import APIConfig
from ratewatch.models.health import APIStatus, StatusLevel, WindowType


class RateCounter:
    def __init__(self, redis: aioredis.Redis, key_prefix: str) -> None:
        self.redis = redis
        self.key_prefix = key_prefix

    # --- Fixed window ---

    def _fixed_key(self, api_name: str, window_seconds: int) -> str:
        window_start = int(time.time() // window_seconds * window_seconds)
        return f"{self.key_prefix}:{api_name}:{window_start}"

    async def _increment_fixed(self, api_name: str, window_seconds: int) -> int:
        key = self._fixed_key(api_name, window_seconds)
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        results = await pipe.execute()
        return int(results[0])

    async def _count_fixed(self, api_name: str, window_seconds: int) -> int:
        key = self._fixed_key(api_name, window_seconds)
        val = await self.redis.get(key)
        return int(val) if val else 0

    async def _ttl_fixed(self, api_name: str, window_seconds: int) -> int | None:
        key = self._fixed_key(api_name, window_seconds)
        ttl = await self.redis.ttl(key)
        return ttl if ttl > 0 else None

    # --- Sliding window ---

    def _sliding_key(self, api_name: str) -> str:
        return f"{self.key_prefix}:sliding:{api_name}"

    async def _increment_sliding(self, api_name: str, window_seconds: int) -> int:
        key = self._sliding_key(api_name)
        now = time.time()
        cutoff = now - window_seconds
        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, "-inf", cutoff)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        results = await pipe.execute()
        return int(results[2])

    async def _count_sliding(self, api_name: str, window_seconds: int) -> int:
        key = self._sliding_key(api_name)
        cutoff = time.time() - window_seconds
        await self.redis.zremrangebyscore(key, "-inf", cutoff)
        return await self.redis.zcard(key)

    # --- Public interface ---

    async def increment(self, api: APIConfig) -> int:
        if api.window_type == WindowType.SLIDING:
            return await self._increment_sliding(api.name, api.window_seconds)
        return await self._increment_fixed(api.name, api.window_seconds)

    async def get_status(self, api: APIConfig) -> APIStatus:
        if api.window_type == WindowType.SLIDING:
            count = await self._count_sliding(api.name, api.window_seconds)
            reset_in = None
        else:
            count = await self._count_fixed(api.name, api.window_seconds)
            reset_in = await self._ttl_fixed(api.name, api.window_seconds)

        remaining = max(api.limit - count, 0)
        usage_percent = round(count / api.limit * 100, 1)
        status = _compute_status(usage_percent, api.alert_threshold)

        return APIStatus(
            api_name=api.name,
            current_count=count,
            limit=api.limit,
            remaining=remaining,
            usage_percent=usage_percent,
            window_seconds=api.window_seconds,
            reset_in_seconds=reset_in,
            status=status,
        )


def _compute_status(usage_percent: float, alert_threshold: float) -> StatusLevel:
    if usage_percent >= 100:
        return StatusLevel.EXHAUSTED
    if usage_percent >= 90:
        return StatusLevel.CRITICAL
    if usage_percent >= alert_threshold * 100:
        return StatusLevel.WARNING
    return StatusLevel.OK
