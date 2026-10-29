"""Command-line interface for the API monitor."""

import argparse
import asyncio
import sys

from api_monitor.checker import check_all
from api_monitor.config import ConfigError, load_config, validate_config
from api_monitor.database import availability, initialize, recent_checks, save_results
from api_monitor.models import MonitorConfig, Target


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check HTTP endpoints and record their status.")
    parser.add_argument("--config", help="JSON config file")
    parser.add_argument("--url", action="append", help="URL to check; can be repeated")
    parser.add_argument("--timeout", type=float, help="Per-request timeout in seconds")
    parser.add_argument("--retries", type=int, help="Maximum retries for transient failures")
    parser.add_argument("--backoff", type=float, help="Initial retry delay in seconds")
    parser.add_argument("--db", default="monitor.sqlite3", help="SQLite history file")
    parser.add_argument("--history", type=int, metavar="N", help="Show the latest N saved checks")
    return parser.parse_args(argv)


def report(results, database: str) -> bool:
    healthy_all = True
    for result in results:
        status = "UP" if result.healthy else "DOWN"
        detail = f"HTTP {result.status_code}" if result.status_code is not None else (result.error or "No response")
        uptime = availability(database, result.target_name)
        uptime_text = "no history" if uptime is None else f"{uptime:.1f}% recent availability"
        print(f"[{status:4}] {result.target_name}: {detail}; {result.elapsed_ms:.0f} ms; "
              f"{result.attempts} attempt(s); {uptime_text}")
        if result.error and result.status_code is None:
            print(f"       {result.error}")
        healthy_all &= result.healthy
    return healthy_all


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.history is not None:
            if args.history < 1:
                raise ConfigError("--history must be at least 1.")
            for row in recent_checks(args.db, args.history):
                name, checked, healthy, status, elapsed, attempts, error = row
                print(f"{'UP' if healthy else 'DOWN':4} {name} {checked} HTTP={status} "
                      f"{elapsed:.0f}ms attempts={attempts} {error or ''}")
            return 0

        if args.config:
            config = load_config(args.config)
        elif args.url:
            config = MonitorConfig(tuple(Target(name=url, url=url) for url in args.url))
        else:
            config = load_config("config.example.json")
        config = MonitorConfig(
            targets=config.targets,
            timeout_seconds=args.timeout if args.timeout is not None else config.timeout_seconds,
            max_retries=args.retries if args.retries is not None else config.max_retries,
            backoff_seconds=args.backoff if args.backoff is not None else config.backoff_seconds,
        )
        validate_config(config)
        initialize(args.db)
        results = asyncio.run(check_all(config))
        save_results(args.db, results)
        return 0 if report(results, args.db) else 1
    except (ConfigError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
