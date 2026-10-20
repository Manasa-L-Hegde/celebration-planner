"""Celebration & Event Planner: application factory."""
from __future__ import annotations

from datetime import date, datetime
from typing import Callable, Optional
from zoneinfo import ZoneInfo

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .ai import GeminiProvider, InsightsProvider, InsightsService, load_system_prompt
from .config import Settings, load_settings
from .routes import bp
from .security import RateLimiter, apply_security_headers


def create_app(
    settings: Optional[Settings] = None,
    provider: Optional[InsightsProvider] = None,
    today_fn: Optional[Callable[[], date]] = None,
) -> Flask:
    """Create the Flask app.

    ``provider`` and ``today_fn`` can be injected so tests never touch the network or the clock.
    Without an API key (and no injected provider) the app serves deterministic fallback insights.
    """
    settings = settings or load_settings()
    app = Flask(__name__)
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["MAX_CONTENT_LENGTH"] = settings.max_request_bytes
    app.json.sort_keys = False
    if settings.trust_proxy:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)  # type: ignore[method-assign]

    tz = ZoneInfo(settings.timezone)
    if provider is None and settings.gemini_api_key:
        provider = GeminiProvider(
            settings.gemini_api_key, settings.gemini_model, load_system_prompt(), settings.gemini_timeout_ms
        )

    app.extensions["settings"] = settings
    app.extensions["today_fn"] = today_fn or (lambda: datetime.now(tz).date())
    app.extensions["rate_limiter"] = RateLimiter(settings.rate_limit_per_minute, 60.0)
    app.extensions["insights"] = InsightsService(provider, settings.cache_size)

    app.register_blueprint(bp)
    app.after_request(apply_security_headers)
    return app
