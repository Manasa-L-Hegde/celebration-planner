"""Tests for services layer (planner_service and ai_service)."""
from __future__ import annotations

from datetime import date

from app.ai import InsightsService
from app.models import PlanRequest
from services.ai_service import GeminiProvider, InsightsService as ServiceInsightsService
from services.planner_service import create_plan


def test_services_create_plan(fake_insights_service: InsightsService) -> None:
    request = PlanRequest(
        event_type="wedding",
        title="Pooja and Rahul Wedding",
        guest_count=180,
        budget=1200000,
        event_date=date(2026, 11, 15),
        city="Bengaluru",
        preferences="Traditional South Indian wedding, vegetarian feast",
    )
    today = date(2026, 10, 20)
    result = create_plan(request, today, fake_insights_service)

    # Budget math
    assert sum(line.amount for line in result.budget_lines) == 1200000
    assert result.per_guest == 1200000 // 180
    assert result.days_until == 26
    # AI insights integrated
    assert result.insights.summary
    assert len(result.insights.ideas) >= 1
    assert len(result.insights.checklist_extras) >= 1
    assert len(result.insights.saving_tips) >= 1
    assert result.ai_source == "gemini"


def test_services_ai_service_exports() -> None:
    assert ServiceInsightsService is InsightsService
    assert GeminiProvider is not None
