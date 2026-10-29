import json
import tempfile
import unittest
from pathlib import Path

from api_monitor.config import ConfigError, load_config, validate_config
from api_monitor.models import MonitorConfig, Target


class ConfigTests(unittest.TestCase):
    def test_load_valid_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"targets": [{"name": "local", "url": "http://localhost"}]}))
            self.assertEqual(load_config(path).targets[0].name, "local")

    def test_reject_invalid_scheme(self):
        with self.assertRaises(ConfigError):
            validate_config(MonitorConfig((Target("bad", "ftp://example.com"),)))

    def test_reject_empty_targets(self):
        with self.assertRaises(ConfigError):
            validate_config(MonitorConfig(()))

    def test_report_bad_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text("{")
            with self.assertRaises(ConfigError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()
