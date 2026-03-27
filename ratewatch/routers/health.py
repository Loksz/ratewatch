from datetime import datetime

from fastapi import APIRouter, HTTPException

from ratewatch.dependencies import ConfigDep, RedisDep
from ratewatch.models.health import APIStatus, HealthResponse, StatusLevel
from ratewatch.services.counter import RateCounter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Estado actual de todas las APIs monitoreadas",
)
async def health(config: ConfigDep, redis: RedisDep) -> HealthResponse:
    counter = RateCounter(redis, config.key_prefix)
    statuses: list[APIStatus] = [await counter.get_status(api) for api in config.apis]

    return HealthResponse(
        apis=statuses,
        total_apis=len(statuses),
        apis_ok=sum(1 for s in statuses if s.status == StatusLevel.OK),
        apis_warning=sum(
            1 for s in statuses if s.status in (StatusLevel.WARNING, StatusLevel.CRITICAL)
        ),
        apis_exhausted=sum(1 for s in statuses if s.status == StatusLevel.EXHAUSTED),
        generated_at=datetime.utcnow(),
    )


@router.get(
    "/health/{api_name}",
    response_model=APIStatus,
    summary="Estado de una API específica por nombre",
)
async def health_by_name(api_name: str, config: ConfigDep, redis: RedisDep) -> APIStatus:
    api = next((a for a in config.apis if a.name == api_name), None)
    if api is None:
        raise HTTPException(status_code=404, detail=f"API '{api_name}' no está configurada")

    counter = RateCounter(redis, config.key_prefix)
    return await counter.get_status(api)
