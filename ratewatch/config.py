import os
from functools import lru_cache
from pathlib import Path

import yaml

from ratewatch.models.config import AppConfig


def _load_config(path: str) -> AppConfig:
    raw = Path(path).read_text()
    data = yaml.safe_load(raw)
    return AppConfig.model_validate(data)


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    path = os.getenv("RATEWATCH_CONFIG_PATH", "config.yaml")
    return _load_config(path)
