#!/usr/bin/env python3
"""
Comlina — Uptime Monitor and Health-Check Script
Independent monitoring script that pings the FastAPI backend health endpoint,
measures round-trip latency, handles retries with backoff, and safely logs results.

Usage:
    python scripts/uptime_monitor.py [--url URL] [--timeout SECONDS] [--retries COUNT] [--json]
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("uptime_monitor")

DEFAULT_HEALTH_URL = os.getenv("HEALTH_CHECK_URL", "https://comlina-api.onrender.com/health")
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("HEALTH_CHECK_TIMEOUT", "15.0"))
DEFAULT_MAX_RETRIES = int(os.getenv("HEALTH_CHECK_RETRIES", "3"))
DEFAULT_RETRY_DELAY = float(os.getenv("HEALTH_CHECK_RETRY_DELAY", "3.0"))


def check_health_once(
    url: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS
) -> Tuple[bool, Optional[int], float, Optional[Dict[str, Any]], Optional[str]]:
    """
    Perform a single GET request to the health endpoint.
    Returns: (success, status_code, latency_ms, payload, error_message)
    """
    headers = {
        "User-Agent": "Comlina-Uptime-Monitor/1.0",
        "Accept": "application/json",
        "Cache-Control": "no-cache",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")

    start_time = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status_code = response.getcode()
            body = response.read().decode("utf-8")

            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = None

            is_healthy = (status_code == 200) and (
                isinstance(payload, dict) and payload.get("status") == "healthy"
            )

            if is_healthy:
                return True, status_code, latency_ms, payload, None
            else:
                err_msg = f"Unexpected response: status={status_code}, body={body[:150]}"
                return False, status_code, latency_ms, payload, err_msg

    except urllib.error.HTTPError as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return False, e.code, latency_ms, None, f"HTTP Error {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return False, None, latency_ms, None, f"Network/URL Error: {e.reason}"
    except TimeoutError:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return False, None, latency_ms, None, f"Request timed out after {timeout}s"
    except Exception as e:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return False, None, latency_ms, None, f"Unexpected error: {type(e).__name__}: {str(e)}"


def run_monitor(
    url: str = DEFAULT_HEALTH_URL,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    max_retries: int = DEFAULT_MAX_RETRIES,
    retry_delay: float = DEFAULT_RETRY_DELAY,
) -> Dict[str, Any]:
    """
    Run health check with retry and exponential backoff.
    Returns structured result dictionary.
    """
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    attempts_history = []
    current_delay = retry_delay

    for attempt in range(1, max_retries + 1):
        success, status_code, latency_ms, payload, error = check_health_once(url, timeout=timeout)
        attempt_record = {
            "attempt": attempt,
            "success": success,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "error": error,
        }
        attempts_history.append(attempt_record)

        if success:
            logger.info(
                f"[UPTIME-OK] {url} responded HTTP {status_code} in {latency_ms}ms "
                f"(attempt {attempt}/{max_retries})"
            )
            return {
                "timestamp_utc": timestamp_utc,
                "target_url": url,
                "healthy": True,
                "status_code": status_code,
                "latency_ms": latency_ms,
                "attempts_used": attempt,
                "max_retries": max_retries,
                "payload": payload,
                "history": attempts_history,
                "error": None,
            }

        logger.warning(
            f"[UPTIME-WARN] Attempt {attempt}/{max_retries} failed for {url}: "
            f"{error} (took {latency_ms}ms)"
        )

        if attempt < max_retries:
            time.sleep(current_delay)
            current_delay *= 1.5  # Exponential backoff

    logger.error(
        f"[UPTIME-CRITICAL] All {max_retries} attempts failed for {url}. Last error: {error}"
    )
    return {
        "timestamp_utc": timestamp_utc,
        "target_url": url,
        "healthy": False,
        "status_code": status_code,
        "latency_ms": latency_ms,
        "attempts_used": max_retries,
        "max_retries": max_retries,
        "payload": payload,
        "history": attempts_history,
        "error": error,
    }


def main():
    parser = argparse.ArgumentParser(description="Comlina Health-Check Uptime Monitor")
    parser.add_argument("--url", default=DEFAULT_HEALTH_URL, help="Target health check URL")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="Timeout in seconds")
    parser.add_argument("--retries", type=int, default=DEFAULT_MAX_RETRIES, help="Maximum retry attempts")
    parser.add_argument("--delay", type=float, default=DEFAULT_RETRY_DELAY, help="Base retry delay in seconds")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--log-file", type=str, default=None, help="Optional log file path to record history")

    args = parser.parse_args()
    result = run_monitor(
        url=args.url,
        timeout=args.timeout,
        max_retries=args.retries,
        retry_delay=args.delay,
    )

    if args.log_file:
        try:
            with open(args.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(result) + "\n")
        except Exception as e:
            logger.warning(f"Failed to append to log file {args.log_file}: {e}")

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status_text = "HEALTHY" if result["healthy"] else "UNHEALTHY"
        print(
            f"\nResult: {status_text} | Status: {result['status_code']} | "
            f"Latency: {result['latency_ms']}ms | Attempts: {result['attempts_used']}/{result['max_retries']}"
        )

    sys.exit(0 if result["healthy"] else 1)


if __name__ == "__main__":
    main()
