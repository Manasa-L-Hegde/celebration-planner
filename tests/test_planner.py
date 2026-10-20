from datetime import timedelta

import pytest

from app.planner import (
    PROFILES, PlanInputError, adjusted_splits, allocate_budget, build_core_plan, build_timeline,
)
from conftest import TODAY, make_request


@pytest.mark.parametrize("event_type", ["wedding", "birthday", "community"])
def test_base_splits_total_100(event_type):
    assert sum(PROFILES[event_type].splits.values()) == 100


@pytest.mark.parametrize("budget", [1_000, 1_001, 99_999, 123_457, 1_000_000, 99_999_999])
@pytest.mark.parametrize("event_type", ["wedding", "birthday", "community"])
def test_allocation_sums_exactly_to_budget(event_type, budget):
    lines = allocate_budget(budget, PROFILES[event_type].splits)
    assert sum(line.amount for line in lines) == budget
    assert all(line.amount >= 0 for line in lines)


def test_allocation_rejects_bad_percentages():
    with pytest.raises(ValueError):
        allocate_budget(1000, {"a": 50, "b": 40})


def test_tight_budget_moves_points_to_essential_category():
    request = make_request(guest_count=1000, budget=500_000)  # Rs 500 per guest, tight for a wedding
    splits, notes = adjusted_splits(request, days_until=120)
    base = PROFILES["wedding"].splits
    assert splits["Catering"] == base["Catering"] + 5
    assert splits["Decor & Flowers"] < base["Decor & Flowers"]
    assert any("tight" in n.lower() for n in notes)
    assert sum(splits.values()) == 100


def test_comfortable_budget_keeps_base_split():
    request = make_request(guest_count=100, budget=1_000_000)
    splits, notes = adjusted_splits(request, days_until=120)
    assert splits == PROFILES["wedding"].splits
    assert notes == []


def test_short_notice_and_large_event_raise_contingency():
    request = make_request(guest_count=400, budget=2_000_000)
    splits, notes = adjusted_splits(request, days_until=5)
    assert splits["Contingency"] == PROFILES["wedding"].splits["Contingency"] + 2 + 3
    assert len(notes) == 2
    assert sum(splits.values()) == 100


def test_timeline_is_sorted_and_never_before_today():
    request = make_request(event_date=(TODAY + timedelta(days=200)).isoformat())
    milestones, compressed = build_timeline(request, TODAY)
    dates = [m.due_date for m in milestones]
    assert dates == sorted(dates)
    assert min(dates) >= TODAY
    assert compressed is False


def test_timeline_compresses_when_lead_time_is_short():
    request = make_request(event_date=(TODAY + timedelta(days=20)).isoformat())
    milestones, compressed = build_timeline(request, TODAY)
    assert compressed is True
    assert min(m.due_date for m in milestones) >= TODAY
    event_day = [m for m in milestones if m.category == "Event day"][0]
    assert event_day.due_date == request.event_date


def test_same_day_event_is_allowed():
    plan = build_core_plan(make_request(event_date=TODAY.isoformat()), TODAY)
    assert plan.days_until == 0
    assert any("compressed" in w for w in plan.warnings)


def test_past_date_is_rejected():
    request = make_request(event_date=(TODAY - timedelta(days=1)).isoformat())
    with pytest.raises(PlanInputError) as info:
        build_core_plan(request, TODAY)
    assert info.value.field == "event_date"


def test_far_future_date_is_rejected():
    request = make_request(event_date=(TODAY + timedelta(days=365 * 4)).isoformat())
    with pytest.raises(PlanInputError):
        build_core_plan(request, TODAY)


def test_core_plan_contents():
    plan = build_core_plan(make_request(guest_count=200, budget=1_000_000), TODAY)
    assert plan.per_guest == 5000
    assert plan.vendor_checklist and all(g.items for g in plan.vendor_checklist)
    assert sum(line.amount for line in plan.budget_lines) == 1_000_000
