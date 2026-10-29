"""Data models shared by the monitor modules."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Target:
    name: str
    url: str


@dataclass(frozen=True)
class MonitorConfig:
    targets: tuple[Target, ...]
    timeout_seconds: float = 5.0
    max_retries: int = 2
    backoff_seconds: float = 0.5


@dataclass(frozen=True)
class CheckResult:
    target_name: str
    url: str
    checked_at: str
    healthy: bool
    status_code: int | None
    elapsed_ms: float
    attempts: int
    error: str | None = None

    @classmethod
    def now(cls, **values) -> "CheckResult":
        """Create a result with a timezone-aware UTC timestamp."""
        return cls(checked_at=datetime.now(timezone.utc).isoformat(), **values)
