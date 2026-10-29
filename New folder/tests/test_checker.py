import asyncio
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from api_monitor.checker import check_target
from api_monitor.models import MonitorConfig, Target


class Handler(BaseHTTPRequestHandler):
    status = 200

    def do_GET(self):
        self.send_response(self.status)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args):
        pass


class CheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/health"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_successful_check(self):
        Handler.status = 200
        result = asyncio.run(check_target(Target("local", self.url), MonitorConfig((Target("local", self.url),))))
        self.assertTrue(result.healthy)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.attempts, 1)

    def test_server_error_retries(self):
        Handler.status = 503
        target = Target("local", self.url)
        result = asyncio.run(check_target(target, MonitorConfig((target,), max_retries=1, backoff_seconds=0)))
        self.assertFalse(result.healthy)
        self.assertEqual(result.status_code, 503)
        self.assertEqual(result.attempts, 2)


if __name__ == "__main__":
    unittest.main()
