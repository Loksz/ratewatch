from typing import Annotated

import httpx
import redis.asyncio as aioredis
from fastapi import Depends, Request

from ratewatch.config import get_config
from ratewatch.models.config import AppConfig


def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis


def get_proxy_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


# Type aliases for cleaner router signatures
ConfigDep = Annotated[AppConfig, Depends(get_config)]
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]
ClientDep = Annotated[httpx.AsyncClient, Depends(get_proxy_client)]
