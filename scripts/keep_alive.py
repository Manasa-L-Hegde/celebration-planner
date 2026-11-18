"""Manual or scheduled keep-alive ping for the Celebration Planner live site."""
import logging
import sys
import time
import urllib.request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

TARGET_URL = "https://celebration-planner.onrender.com/healthz"


def ping_once(url: str = TARGET_URL) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KeepAliveScript/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            logging.info("Pinged %s successfully (status %d)", url, resp.status)
            return resp.status == 200
    except Exception as exc:
        logging.error("Ping to %s failed: %s", url, exc)
        return False


def run_loop(interval_seconds: int = 600) -> None:
    logging.info("Starting keep-alive loop (interval: %ds)... Press Ctrl+C to stop.", interval_seconds)
    while True:
        ping_once()
        time.sleep(interval_seconds)


if __name__ == "__main__":
    if "--loop" in sys.argv:
        run_loop()
    else:
        success = ping_once()
        sys.exit(0 if success else 1)
