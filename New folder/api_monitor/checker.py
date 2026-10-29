"""Asynchronous HTTP checks with bounded retry and timeout behavior."""

import asyncio
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from api_monitor.models import CheckResult, MonitorConfig, Target

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _request(target: Target, timeout: float) -> tuple[int, float]:
    request = Request(target.url, headers={"User-Agent": "resilient-api-monitor/1.0"}, method="GET")
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, (time.perf_counter() - started) * 1000
    except HTTPError as exc:
        # HTTPError is also a response: preserve its status for reporting/retry.
        return exc.code, (time.perf_counter() - started) * 1000


async def check_target(target: Target, config: MonitorConfig) -> CheckResult:
    """Check one target, retrying transient network and server failures."""
    last_status: int | None = None
    last_error: str | None = None
    elapsed_ms = 0.0
    total_attempts = config.max_retries + 1

    for attempt in range(1, total_attempts + 1):
        try:
            status, elapsed_ms = await asyncio.wait_for(
                asyncio.to_thread(_request, target, config.timeout_seconds),
                timeout=config.timeout_seconds + 0.25,
            )
            last_status = status
            last_error = None if 200 <= status < 400 else f"HTTP {status}"
            if 200 <= status < 400:
                return CheckResult.now(
                    target_name=target.name, url=target.url, healthy=True,
                    status_code=status, elapsed_ms=elapsed_ms, attempts=attempt,
                )
            retryable = status in RETRYABLE_STATUS_CODES
        except (TimeoutError, asyncio.TimeoutError) as exc:
            last_error = f"Request timed out after {config.timeout_seconds:g}s"
            retryable = True
        except (URLError, OSError, ValueError) as exc:
            last_error = f"Network error: {exc}"
            retryable = True

        if not retryable or attempt == total_attempts:
            return CheckResult.now(
                target_name=target.name, url=target.url, healthy=False,
                status_code=last_status, elapsed_ms=elapsed_ms, attempts=attempt,
                error=last_error,
            )
        delay = min(config.backoff_seconds * (2 ** (attempt - 1)), 10.0)
        await asyncio.sleep(delay)

    raise AssertionError("Retry loop exited unexpectedly")


async def check_all(config: MonitorConfig) -> list[CheckResult]:
    """Check all configured targets concurrently."""
    return await asyncio.gather(*(check_target(target, config) for target in config.targets))
