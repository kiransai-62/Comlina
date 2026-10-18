"""
Tests for Comlina Health Endpoint and Uptime Monitoring System.
Verifies:
1. GET /health and /api/v1/health responses and security.
2. scripts/uptime_monitor.py successful checks, latency tracking, retry logic,
   timeout handling, and transient failure recovery.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import urllib.error
from fastapi.testclient import TestClient

# Ensure repo root and server are on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SERVER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

from app.main import app
from scripts.uptime_monitor import check_health_once, run_monitor


class TestHealthEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint_returns_200_and_healthy_status(self):
        """GET /health must return 200 and healthy JSON response."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "comlina-api")
        self.assertIn("version", data)
        self.assertIn("meta_api_version", data)

    def test_api_v1_health_alias(self):
        """GET /api/v1/health alias must also return 200."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "healthy")

    def test_health_endpoint_head_method(self):
        """HEAD /health must return 200 with empty body."""
        response = self.client.head("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")

    def test_health_endpoint_does_not_leak_secrets(self):
        """Ensure response payload contains no environment variables or internal credentials."""
        response = self.client.get("/health")
        body_text = response.text.lower()
        forbidden_keywords = [
            "password", "secret", "token", "database_url", "postgres",
            "redis", "encryption_key", "supabase_jwt"
        ]
        for keyword in forbidden_keywords:
            self.assertNotIn(keyword, body_text)

    def test_health_endpoint_exempt_from_rate_limiting(self):
        """Multiple consecutive requests to /health must not be blocked by rate limiting."""
        for _ in range(25):
            res = self.client.get("/health")
            self.assertEqual(res.status_code, 200)


class TestUptimeMonitorScript(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_monitor_successful_check(self, mock_urlopen):
        """Uptime monitor records status 200, valid latency, and payload."""
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = json.dumps({
            "status": "healthy",
            "service": "comlina-api",
            "version": "1.0.0"
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = run_monitor(url="https://fake-comlina.com/health", max_retries=1)

        self.assertTrue(result["healthy"])
        self.assertEqual(result["status_code"], 200)
        self.assertGreaterEqual(result["latency_ms"], 0)
        self.assertEqual(result["attempts_used"], 1)
        self.assertIsNone(result["error"])
        self.assertEqual(result["payload"]["status"], "healthy")

    @patch("urllib.request.urlopen")
    @patch("time.sleep")
    def test_monitor_transient_failure_and_retry_success(self, mock_sleep, mock_urlopen):
        """Monitor recovers when initial attempt returns 503 and subsequent attempt returns 200."""
        # Attempt 1 raises 503 Bad Gateway, Attempt 2 succeeds
        mock_resp_success = MagicMock()
        mock_resp_success.getcode.return_value = 200
        mock_resp_success.read.return_value = json.dumps({"status": "healthy"}).encode("utf-8")

        err_503 = urllib.error.HTTPError(
            url="https://fake-comlina.com/health",
            code=503,
            msg="Service Unavailable",
            hdrs={},
            fp=None,
        )

        mock_urlopen.side_effect = [
            err_503,
            MagicMock(__enter__=MagicMock(return_value=mock_resp_success)),
        ]

        result = run_monitor(url="https://fake-comlina.com/health", max_retries=3, retry_delay=0.01)

        self.assertTrue(result["healthy"])
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["attempts_used"], 2)
        self.assertEqual(len(result["history"]), 2)
        self.assertFalse(result["history"][0]["success"])
        self.assertTrue(result["history"][1]["success"])
        mock_sleep.assert_called_once()

    @patch("urllib.request.urlopen")
    @patch("time.sleep")
    def test_monitor_timeout_handling(self, mock_sleep, mock_urlopen):
        """Monitor safely catches TimeoutError without crashing and reports failure."""
        mock_urlopen.side_effect = TimeoutError("Connection timed out")

        result = run_monitor(url="https://fake-comlina.com/health", timeout=2.0, max_retries=2, retry_delay=0.01)

        self.assertFalse(result["healthy"])
        self.assertIsNone(result["status_code"])
        self.assertEqual(result["attempts_used"], 2)
        self.assertIn("timed out", result["error"].lower())
        self.assertEqual(len(result["history"]), 2)
        self.assertFalse(result["history"][0]["success"])

    @patch("urllib.request.urlopen")
    @patch("time.sleep")
    def test_monitor_http_500_failure(self, mock_sleep, mock_urlopen):
        """Monitor records HTTP 500 failure across all retries."""
        err_500 = urllib.error.HTTPError(
            url="https://fake-comlina.com/health",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None,
        )
        mock_urlopen.side_effect = err_500

        result = run_monitor(url="https://fake-comlina.com/health", max_retries=2, retry_delay=0.01)

        self.assertFalse(result["healthy"])
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["attempts_used"], 2)
        self.assertIn("500", result["error"])

    @patch("urllib.request.urlopen")
    def test_monitor_unhealthy_payload_status(self, mock_urlopen):
        """If HTTP is 200 but status field is 'degraded' or missing, health check fails."""
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = json.dumps({"status": "degraded"}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = run_monitor(url="https://fake-comlina.com/health", max_retries=1)

        self.assertFalse(result["healthy"])
        self.assertEqual(result["status_code"], 200)
        self.assertIn("Unexpected response", result["error"])

    @patch("urllib.request.urlopen")
    def test_monitor_dns_resolution_failure(self, mock_urlopen):
        """If DNS fails (URLError), monitor handles it cleanly without crashing."""
        mock_urlopen.side_effect = urllib.error.URLError("[Errno 11001] getaddrinfo failed")

        result = run_monitor(url="https://non-existent-domain-xyz.com/health", max_retries=1)

        self.assertFalse(result["healthy"])
        self.assertIsNone(result["status_code"])
        self.assertIn("Network/URL Error", result["error"])


if __name__ == "__main__":
    unittest.main()
