import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ratewatch.dependencies import ConfigDep, RedisDep
from ratewatch.services.counter import RateCounter

router = APIRouter(tags=["events"])


@router.get(
    "/events",
    summary="Stream SSE con el estado de todas las APIs",
    response_description="text/event-stream indefinido — un evento JSON por intervalo",
)
async def sse_events(request: Request, config: ConfigDep, redis: RedisDep) -> StreamingResponse:
    async def generate():
        counter = RateCounter(redis, config.key_prefix)
        iteration = 0
        try:
            while True:
                await asyncio.sleep(config.sse_interval)

                statuses = [await counter.get_status(api) for api in config.apis]
                payload = json.dumps({"apis": [s.model_dump() for s in statuses]})
                yield f"data: {payload}\n\n"

                iteration += 1
                if iteration % 15 == 0:
                    yield ": keep-alive\n\n"

        except asyncio.CancelledError:
            return

    return StreamingResponse(generate(), media_type="text/event-stream")
