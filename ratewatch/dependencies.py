from typing import Annotated

import httpx
import redis.asyncio as aioredis
from fastapi import Depends

from ratewatch.config import get_config
from ratewatch.models.config import AppConfig


def get_redis() -> aioredis.Redis:
    config = get_config()
    return aioredis.from_url(config.redis_url, decode_responses=True)


async def get_proxy_client() -> httpx.AsyncClient:
    async with httpx.AsyncClient() as client:
        yield client


# Type aliases for cleaner router signatures
ConfigDep = Annotated[AppConfig, Depends(get_config)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]
ClientDep = Annotated[httpx.AsyncClient, Depends(get_proxy_client)]
