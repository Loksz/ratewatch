from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])

_DASHBOARD = Path(__file__).parent.parent.parent / "static" / "dashboard.html"


@router.get("/", response_class=HTMLResponse, summary="Dashboard de monitoreo en tiempo real")
async def dashboard() -> HTMLResponse:
    return HTMLResponse(content=_DASHBOARD.read_text())
