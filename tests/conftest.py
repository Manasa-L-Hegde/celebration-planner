"""Shared fixtures: deterministic clock and an injectable fake AI provider."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from app import create_app
from app.config import Settings
from app.models import AIInsights, ChecklistExtra, CorePlan, Idea, PlanRequest

TODAY = date(2026, 10, 20)


class FakeProvider:
    """Counts calls and returns canned insights."""

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: PlanRequest, core: CorePlan) -> AIInsights:
        self.calls += 1
        return AIInsights(
            summary="A lovely plan.",
            ideas=[Idea(title="Idea", description="Do something nice.")],
            checklist_extras=[ChecklistExtra(category="Misc", item="Check the weather")],
            saving_tips=["Compare quotes."],
        )


def make_payload(**overrides) -> dict:
    payload = {
        "event_type": "wedding",
        "title": "Aarav and Diya",
        "guest_count": 200,
        "budget": 1_000_000,
        "event_date": (TODAY + timedelta(days=120)).isoformat(),
        "city": "Bengaluru",
        "preferences": "vegetarian menu",
    }
    payload.update(overrides)
    return payload


def make_request(**overrides) -> PlanRequest:
    return PlanRequest.model_validate(make_payload(**overrides))


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def fake_insights_service(provider: FakeProvider):
    from app.ai import InsightsService
    return InsightsService(provider=provider, cache_size=32)


@pytest.fixture
def client(provider):
    app = create_app(
        Settings(rate_limit_per_minute=1000), provider=provider, today_fn=lambda: TODAY
    )
    return app.test_client()
