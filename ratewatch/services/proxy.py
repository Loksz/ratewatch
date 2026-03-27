import httpx
from fastapi import Request, Response

from ratewatch.models.config import APIConfig

# Headers that must not be forwarded to the external API
_HOP_BY_HOP = {
    "host",
    "content-length",
    "transfer-encoding",
    "connection",
    "keep-alive",
    "upgrade",
    "proxy-authorization",
}


class ProxyService:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self.client = client

    async def forward(
        self,
        request: Request,
        rest_of_path: str,
        api: APIConfig,
        current_count: int,
    ) -> Response:
        target_url = _build_url(api, rest_of_path, str(request.url.query))
        headers = _filter_headers(dict(request.headers), api.headers)
        body = await request.body()

        try:
            upstream = await self.client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                timeout=api.timeout,
            )
        except httpx.TimeoutException:
            return Response(status_code=504, content=b"Gateway Timeout")

        response_headers = dict(upstream.headers)
        response_headers["X-Ratewatch-Count"] = str(current_count)
        response_headers["X-Ratewatch-Remaining"] = str(max(api.limit - current_count, 0))

        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
            media_type=upstream.headers.get("content-type"),
        )


def _build_url(api: APIConfig, rest_of_path: str, query_string: str) -> str:
    base = str(api.base_url).rstrip("/")
    path = rest_of_path.lstrip("/")
    url = f"{base}/{path}"
    if query_string:
        url = f"{url}?{query_string}"
    return url


def _filter_headers(
    incoming: dict[str, str],
    api_headers: dict[str, str],
) -> dict[str, str]:
    filtered = {k: v for k, v in incoming.items() if k.lower() not in _HOP_BY_HOP}
    filtered.update(api_headers)
    return filtered
