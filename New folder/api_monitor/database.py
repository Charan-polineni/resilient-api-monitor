"""SQLite persistence for checks and availability summaries."""

import sqlite3
from pathlib import Path

from api_monitor.models import CheckResult


def initialize(database: str | Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY,
            target_name TEXT NOT NULL,
            url TEXT NOT NULL,
            checked_at TEXT NOT NULL,
            healthy INTEGER NOT NULL,
            status_code INTEGER,
            elapsed_ms REAL NOT NULL,
            attempts INTEGER NOT NULL,
            error TEXT
        )""")
        connection.execute("CREATE INDEX IF NOT EXISTS checks_target_time ON checks(target_name, checked_at)")


def save_results(database: str | Path, results: list[CheckResult]) -> None:
    with sqlite3.connect(database) as connection:
        connection.executemany(
            """INSERT INTO checks
            (target_name, url, checked_at, healthy, status_code, elapsed_ms, attempts, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [(r.target_name, r.url, r.checked_at, int(r.healthy), r.status_code,
              r.elapsed_ms, r.attempts, r.error) for r in results],
        )


def recent_checks(database: str | Path, limit: int = 10) -> list[tuple]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    with sqlite3.connect(database) as connection:
        return connection.execute(
            "SELECT target_name, checked_at, healthy, status_code, elapsed_ms, attempts, error "
            "FROM checks ORDER BY id DESC LIMIT ?", (limit,),
        ).fetchall()


def availability(database: str | Path, target_name: str, limit: int = 100) -> float | None:
    """Return recent success percentage, or None when there is no history."""
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            "SELECT AVG(healthy) FROM (SELECT healthy FROM checks "
            "WHERE target_name = ? ORDER BY id DESC LIMIT ?)", (target_name, limit),
        ).fetchone()
    return None if row[0] is None else float(row[0]) * 100
