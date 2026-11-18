"""Background keep-alive ping to prevent free-tier hosts (e.g. Render) from sleeping."""
from __future__ import annotations

import logging
import threading
import time
import urllib.request

logger = logging.getLogger(__name__)

_ping_started = False
_lock = threading.Lock()


def start_keep_alive(url: str, interval_seconds: int = 600) -> None:
    """Launch a daemon thread that periodically pings the public health check endpoint."""
    global _ping_started
    with _lock:
        if _ping_started:
            return
        _ping_started = True

    def _loop() -> None:
        # Initial wait of 20 seconds so server startup completes before first ping
        time.sleep(20)
        while True:
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "CelebrationPlanner-KeepAlive/1.0"},
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    logger.debug("Keep-alive ping to %s succeeded with status %s", url, resp.status)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Keep-alive ping to %s failed: %s", url, exc)
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_loop, name="keep-alive-pinger", daemon=True)
    thread.start()
