from contextlib import asynccontextmanager

import httpx
import redis.asyncio as aioredis
from fastapi import FastAPI

from ratewatch.config import get_config
from ratewatch.routers import dashboard, events, health, proxy


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    app.state.redis = aioredis.from_url(config.redis_url, decode_responses=True)
    app.state.http_client = httpx.AsyncClient()
    try:
        await app.state.redis.ping()
    except Exception as exc:
        raise RuntimeError(f"No se pudo conectar a Redis: {exc}") from exc
    yield
    await app.state.http_client.aclose()
    await app.state.redis.aclose()


app = FastAPI(
    title="Ratewatch",
    description="Proxy middleware que monitorea límites de API en tiempo real",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(proxy.router)
app.include_router(health.router)
app.include_router(events.router)
app.include_router(dashboard.router)
