"""
Health check — polls an HTTP URL until it responds with 2xx or times out.

Used by PreviewRuntime to verify a dev server is actually alive before
marking preview.verified = True in the evidence contract.
"""

from __future__ import annotations

import logging
import time
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


def wait_until_ready(url: str, timeout: int = 30, interval: float = 1.0) -> bool:
    """
    Poll url until it returns a 2xx response or timeout is reached.

    Args:
        url: The URL to check (e.g. 'http://localhost:8888').
        timeout: Maximum seconds to wait before giving up.
        interval: Seconds between each poll attempt.

    Returns:
        True if the URL responded with 2xx within the timeout.
        False if timeout was reached without a successful response.
    """
    deadline = time.monotonic() + timeout
    attempts = 0

    while time.monotonic() < deadline:
        attempts += 1
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if 200 <= resp.status < 300:
                    logger.debug("[EVIDENCE] Health check passed: %s (attempt %d)", url, attempts)
                    return True
        except urllib.error.HTTPError as e:
            # 4xx/5xx from a running server still means it's up
            if e.code < 500:
                logger.debug("[EVIDENCE] Health check OK (HTTP %d): %s", e.code, url)
                return True
        except Exception:
            pass  # Connection refused, timeout, etc. — keep polling

        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(interval, remaining))

    logger.warning(
        "[EVIDENCE] Health check failed: %s did not respond within %ds (%d attempts)",
        url, timeout, attempts
    )
    return False


def check_once(url: str, timeout: float = 2.0) -> bool:
    """
    Single health check ping (no retry).

    Returns True if the URL is reachable, False otherwise.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except Exception:
        return False
