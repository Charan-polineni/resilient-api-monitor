import tempfile
import unittest
from pathlib import Path

from api_monitor.database import availability, initialize, recent_checks, save_results
from api_monitor.models import CheckResult


class DatabaseTests(unittest.TestCase):
    def test_store_history_and_compute_availability(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "test.sqlite3"
            initialize(database)
            save_results(database, [
                CheckResult("service", "http://localhost", "2026-01-01T00:00:00+00:00", True, 200, 8, 1),
                CheckResult("service", "http://localhost", "2026-01-01T00:01:00+00:00", False, 503, 9, 2, "HTTP 503"),
            ])
            self.assertEqual(len(recent_checks(database, 10)), 2)
            self.assertEqual(availability(database, "service"), 50.0)
            self.assertIsNone(availability(database, "missing"))


if __name__ == "__main__":
    unittest.main()
