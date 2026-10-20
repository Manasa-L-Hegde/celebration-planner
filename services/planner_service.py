"""Planner service: orchestrates deterministic math, milestones and vendor items.

Provides the service boundary between HTTP/API layers and the domain models.
"""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from app.models import PlanRequest, PlanResult
from app.planner import build_core_plan

if TYPE_CHECKING:
    from app.ai import InsightsService


def create_plan(request: PlanRequest, today: date, insights_service: InsightsService) -> PlanResult:
    """Build a complete, validated celebration plan.

    Combines deterministic budget calculations, compressed timeline scheduling,
    and vendor checklists with AI-generated theme ideas and money-saving tips.

    Args:
        request: The validated user request data.
        today: The reference date for timeline calculations (in Asia/Kolkata timezone).
        insights_service: Service instance providing AI or fallback insights.

    Returns:
        PlanResult: Full plan ready to be serialized to JSON.
    """
    core = build_core_plan(request, today)
    insights, source = insights_service.get(request, core)
    return PlanResult(
        title=request.title,
        event_type=request.event_type,
        event_date=request.event_date,
        city=request.city,
        guest_count=request.guest_count,
        budget=request.budget,
        days_until=core.days_until,
        per_guest=core.per_guest,
        budget_lines=core.budget_lines,
        milestones=core.milestones,
        vendor_checklist=core.vendor_checklist,
        warnings=core.warnings,
        insights=insights,
        ai_source=source,
    )
