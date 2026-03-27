from fastapi import APIRouter, HTTPException, Request, Response

from ratewatch.dependencies import ClientDep, ConfigDep, RedisDep
from ratewatch.services.counter import RateCounter
from ratewatch.services.proxy import ProxyService

router = APIRouter(prefix="/proxy", tags=["proxy"])


@router.api_route(
    "/{api_name}/{rest_of_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    summary="Proxy transparente a la API configurada",
    response_description="Respuesta de la API externa con headers X-Ratewatch-*",
)
async def proxy_request(
    api_name: str,
    rest_of_path: str,
    request: Request,
    config: ConfigDep,
    redis: RedisDep,
    client: ClientDep,
) -> Response:
    api = next((a for a in config.apis if a.name == api_name), None)
    if api is None:
        raise HTTPException(status_code=404, detail=f"API '{api_name}' no está configurada")

    counter = RateCounter(redis, config.key_prefix)
    current_count = await counter.increment(api)

    service = ProxyService(client)
    return await service.forward(request, rest_of_path, api, current_count)
