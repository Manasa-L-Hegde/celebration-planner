"""Input sanitisation, prompt-injection screening, rate limiting and HTTP headers."""
from __future__ import annotations

import re
import threading
import time
import unicodedata
from collections import deque
from typing import Callable

from flask import Response, request

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_ANGLE_BRACKETS = re.compile(r"[<>]")
_WHITESPACE = re.compile(r"\s+")

_INJECTION_PATTERN = re.compile(
    r"(ignore|disregard|forget|override)\s+(all\s+|any\s+|the\s+|your\s+|previous\s+|prior\s+|above\s+)*"
    r"(instructions?|prompts?|rules?)"
    r"|system\s+prompt|developer\s+message"
    r"|you\s+are\s+now"
    r"|reveal\s+(your|the)\s+(prompt|instructions)",
    re.IGNORECASE,
)


def clean_text(value: str) -> str:
    """Normalise free text: Unicode NFKC, no control chars or angle brackets, collapsed spaces."""
    text = unicodedata.normalize("NFKC", value)
    text = _CONTROL_CHARS.sub(" ", text)
    text = _ANGLE_BRACKETS.sub("", text)
    return _WHITESPACE.sub(" ", text).strip()


def looks_like_injection(value: str) -> bool:
    """Return True when text resembles an attempt to override model instructions."""
    return bool(_INJECTION_PATTERN.search(value))


class RateLimiter:
    """Thread-safe sliding-window rate limiter keyed by client identifier."""

    _SWEEP_THRESHOLD = 5_000

    def __init__(
        self,
        limit: int,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> tuple[bool, int]:
        """Record a hit. Returns ``(allowed, retry_after_seconds)``."""
        now = self._clock()
        with self._lock:
            if len(self._hits) > self._SWEEP_THRESHOLD:
                self._sweep(now)
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] >= self._window:
                hits.popleft()
            if len(hits) >= self._limit:
                retry_after = max(1, int(self._window - (now - hits[0])) + 1)
                return False, retry_after
            hits.append(now)
            return True, 0

    def _sweep(self, now: float) -> None:
        stale = [k for k, h in self._hits.items() if not h or now - h[-1] >= self._window]
        for key in stale:
            del self._hits[key]


_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data:; "
    "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)


def apply_security_headers(response: Response) -> Response:
    """Attach defensive HTTP headers to every response."""
    response.headers["Content-Security-Policy"] = _CSP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response
