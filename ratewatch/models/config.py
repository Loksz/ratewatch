from pydantic import BaseModel, HttpUrl, field_validator

from ratewatch.models.health import WindowType


class APIConfig(BaseModel):
    name: str
    base_url: HttpUrl
    limit: int
    window_seconds: int
    window_type: WindowType = WindowType.FIXED
    alert_threshold: float = 0.8
    timeout: int = 10
    headers: dict[str, str] = {}

    @field_validator("limit", "window_seconds")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be greater than 0")
        return v

    @field_validator("alert_threshold")
    @classmethod
    def threshold_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("must be between 0.0 and 1.0")
        return v


class AppConfig(BaseModel):
    apis: list[APIConfig]
    redis_url: str = "redis://localhost:6379"
    sse_interval: float = 1.0
    key_prefix: str = "ratewatch"
