from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class StatusLevel(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EXHAUSTED = "EXHAUSTED"


class WindowType(str, Enum):
    FIXED = "fixed"
    SLIDING = "sliding"


class APIStatus(BaseModel):
    api_name: str
    current_count: int
    limit: int
    remaining: int
    usage_percent: float
    window_seconds: int
    reset_in_seconds: int | None
    status: StatusLevel


class HealthResponse(BaseModel):
    apis: list[APIStatus]
    total_apis: int
    apis_ok: int
    apis_warning: int
    apis_exhausted: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)
