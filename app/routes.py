"""HTTP routes: the page, a health check and the JSON planning API."""
from __future__ import annotations

from typing import Any, Optional

from flask import Blueprint, Response, current_app, jsonify, render_template, request
from pydantic import ValidationError

from .models import PlanRequest
from .planner import PlanInputError
from .service import create_plan

bp = Blueprint("main", __name__)


def _error(status: int, code: str, message: str, details: Optional[list[dict[str, str]]] = None) -> Response:
    body: dict[str, Any] = {"error": code, "message": message}
    if details:
        body["details"] = details
    response = jsonify(body)
    response.status_code = status
    return response


def _format_errors(exc: ValidationError) -> list[dict[str, str]]:
    """Convert pydantic errors to safe ``{field, message}`` pairs (never echoing input)."""
    details = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"]) or "request"
        message = str(err["msg"]).removeprefix("Value error, ")
        details.append({"field": field, "message": message})
    return details


@bp.get("/")
def index() -> str:
    return render_template("index.html")


@bp.get("/healthz")
def healthz() -> Response:
    return jsonify(status="ok")


@bp.post("/api/plan")
def plan() -> Response:
    allowed, retry_after = current_app.extensions["rate_limiter"].allow(request.remote_addr or "unknown")
    if not allowed:
        response = _error(429, "rate_limited", "Too many requests. Please wait a moment and try again.")
        response.headers["Retry-After"] = str(retry_after)
        return response

    if not request.is_json:
        return _error(415, "unsupported_media_type", "Send the request as application/json.")
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return _error(400, "invalid_json", "The request body must be a JSON object.")

    try:
        plan_request = PlanRequest.model_validate(payload)
    except ValidationError as exc:
        return _error(422, "validation_error", "Please correct the highlighted fields.", _format_errors(exc))

    today = current_app.extensions["today_fn"]()
    try:
        result = create_plan(plan_request, today, current_app.extensions["insights"])
    except PlanInputError as exc:
        return _error(422, "validation_error", "Please correct the highlighted fields.",
                      [{"field": exc.field, "message": str(exc)}])
    return jsonify(result.model_dump(mode="json"))


@bp.app_errorhandler(413)
def too_large(_: Exception) -> Response:
    return _error(413, "payload_too_large", "The request is too large.")


@bp.app_errorhandler(404)
def not_found(_: Exception) -> Response:
    return _error(404, "not_found", "Not found.")


@bp.app_errorhandler(405)
def not_allowed(_: Exception) -> Response:
    return _error(405, "method_not_allowed", "Method not allowed.")
