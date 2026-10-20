import json

from app.ai import (
    FallbackProvider, GeminiProvider, InsightsService, build_user_prompt, load_system_prompt,
    sanitize_insights,
)
from app.models import AIInsights, ChecklistExtra, Idea
from app.planner import build_core_plan
from conftest import TODAY, FakeProvider, make_request


def _core(request=None):
    request = request or make_request()
    return request, build_core_plan(request, TODAY)


class ExplodingProvider:
    def generate(self, request, core):
        raise RuntimeError("boom")


def test_system_prompt_contains_injection_guard():
    prompt = load_system_prompt()
    assert "untrusted" in prompt and "SECURITY RULES" in prompt


def test_user_prompt_wraps_data_and_is_json():
    request, core = _core(make_request(preferences="outdoor"))
    prompt = build_user_prompt(request, core)
    body = prompt.split("<event_data>\n")[1].split("\n</event_data>")[0]
    facts = json.loads(body)
    assert facts["preferences"] == "outdoor"
    assert facts["budget_per_guest_inr"] == core.per_guest


def test_sanitize_caps_lengths_and_strips_markup():
    raw = AIInsights(
        summary="<script>alert(1)</script>" + "x" * 2000,
        ideas=[Idea(title=f"T{i}", description="d") for i in range(20)] + [Idea(title="  ", description="blank")],
        checklist_extras=[ChecklistExtra(category="c", item=f"i{i}") for i in range(30)],
        saving_tips=[f"tip{i}" for i in range(30)],
    )
    clean = sanitize_insights(raw)
    assert "<" not in clean.summary and len(clean.summary) <= 600
    assert len(clean.ideas) == 5 and len(clean.checklist_extras) == 8 and len(clean.saving_tips) == 5


def test_service_uses_fallback_without_provider():
    request, core = _core()
    insights, source = InsightsService(None).get(request, core)
    assert source == "fallback" and insights.ideas


def test_service_falls_back_when_provider_fails():
    request, core = _core()
    insights, source = InsightsService(ExplodingProvider()).get(request, core)
    assert source == "fallback" and insights.summary


def test_service_caches_identical_requests():
    provider = FakeProvider()
    service = InsightsService(provider, cache_size=4)
    request, core = _core()
    assert service.get(request, core)[1] == "gemini"
    service.get(request, core)
    assert provider.calls == 1


def test_cache_is_bounded():
    provider = FakeProvider()
    service = InsightsService(provider, cache_size=2)
    for guests in (10, 20, 30):
        request, core = _core(make_request(guest_count=guests))
        service.get(request, core)
    request, core = _core(make_request(guest_count=10))
    service.get(request, core)  # evicted earlier, so the provider runs again
    assert provider.calls == 4


def test_fallback_echoes_preferences_safely():
    request, core = _core(make_request(preferences="jain menu"))
    insights = FallbackProvider().generate(request, core)
    assert "jain menu" in insights.ideas[0].description


class StubGemini(GeminiProvider):
    def __init__(self, text):
        super().__init__("key", "model", "system")
        self._text = text

    def _call_model(self, prompt):
        return self._text


def test_gemini_provider_parses_valid_json():
    payload = AIInsights(
        summary="ok", ideas=[Idea(title="t", description="d")],
        checklist_extras=[], saving_tips=["s"],
    ).model_dump_json()
    request, core = _core()
    assert StubGemini(payload).generate(request, core).summary == "ok"


def test_invalid_model_json_triggers_fallback():
    request, core = _core()
    insights, source = InsightsService(StubGemini("not json")).get(request, core)
    assert source == "fallback"
