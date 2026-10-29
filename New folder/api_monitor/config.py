"""Load and validate monitor configuration."""

import json
from pathlib import Path
from urllib.parse import urlparse

from api_monitor.models import MonitorConfig, Target


class ConfigError(ValueError):
    """Raised when a configuration file or override is invalid."""


def validate_config(config: MonitorConfig) -> MonitorConfig:
    if not config.targets:
        raise ConfigError("Add at least one target.")
    if config.timeout_seconds <= 0:
        raise ConfigError("timeout_seconds must be greater than zero.")
    if not 0 <= config.max_retries <= 10:
        raise ConfigError("max_retries must be between 0 and 10.")
    if config.backoff_seconds < 0:
        raise ConfigError("backoff_seconds cannot be negative.")
    names: set[str] = set()
    for target in config.targets:
        if not target.name.strip():
            raise ConfigError("Each target needs a non-empty name.")
        if target.name in names:
            raise ConfigError(f"Target names must be unique: {target.name}")
        names.add(target.name)
        parsed = urlparse(target.url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ConfigError(f"Target {target.name!r} must have a valid http(s) URL.")
    return config


def load_config(path: str | Path) -> MonitorConfig:
    """Read JSON configuration and return a validated config object."""
    config_path = Path(path)
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {config_path}: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("Configuration root must be a JSON object.")
    try:
        targets = tuple(Target(name=item["name"], url=item["url"]) for item in raw["targets"])
        config = MonitorConfig(
            targets=targets,
            timeout_seconds=float(raw.get("timeout_seconds", 5)),
            max_retries=int(raw.get("max_retries", 2)),
            backoff_seconds=float(raw.get("backoff_seconds", 0.5)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid configuration fields: {exc}") from exc
    return validate_config(config)
