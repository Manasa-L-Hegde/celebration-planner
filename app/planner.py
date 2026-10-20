"""Deterministic planning logic: budget allocation, timeline and vendor checklist.

Money and dates are computed in plain code (not by the LLM) so results are exact,
reproducible and unit-testable. The LLM only adds ideas and personalisation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .models import BudgetLine, CorePlan, Milestone, PlanRequest, VendorGroup

CONTINGENCY = "Contingency"
MAX_DAYS_AHEAD = 365 * 3
SHORT_NOTICE_DAYS = 14


class PlanInputError(ValueError):
    """Raised when a request is well-formed but cannot be planned (e.g. date in the past)."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


@dataclass(frozen=True)
class EventProfile:
    """Static planning knowledge for one event type."""

    splits: dict[str, int]  # category -> whole percent, must total 100
    essential: str  # category protected when money is tight
    flex: str  # category trimmed first
    min_per_guest: int  # INR below which the budget is considered tight
    large_event_guests: int
    timeline: tuple[tuple[int, str, str], ...]  # (days before event, task, category)
    vendors: tuple[tuple[str, tuple[str, ...]], ...]


PROFILES: dict[str, EventProfile] = {
    "wedding": EventProfile(
        splits={
            "Venue": 22, "Catering": 30, "Decor & Flowers": 10, "Photography & Video": 10,
            "Attire & Beauty": 8, "Entertainment & Music": 5, "Invitations & Stationery": 2,
            "Transport & Logistics": 3, CONTINGENCY: 10,
        },
        essential="Catering", flex="Decor & Flowers", min_per_guest=1500, large_event_guests=300,
        timeline=(
            (180, "Fix budget, draft guest list and lock the date", "Planning"),
            (165, "Book venue and caterer", "Venue"),
            (150, "Book photographer and videographer", "Vendors"),
            (120, "Shop for attire; book makeup and mehendi artists", "Attire"),
            (90, "Send save-the-dates and finalise the decor theme", "Guests"),
            (60, "Send invitations; book music and entertainment", "Guests"),
            (45, "Arrange guest accommodation and transport", "Logistics"),
            (30, "Menu tasting and first headcount estimate", "Catering"),
            (14, "Confirm every vendor in writing; collect RSVPs", "Vendors"),
            (7, "Finalise seating, run-of-show and payment schedule", "Logistics"),
            (2, "Pack an emergency kit and brief family helpers", "Logistics"),
            (0, "Event day: name one point of contact for all vendors", "Event day"),
            (-7, "Send thank-you notes and settle final payments", "After event"),
        ),
        vendors=(
            ("Venue", ("Confirm capacity and date availability", "Ask about power backup, parking and curfew", "Get overtime and cancellation terms in writing")),
            ("Caterer", ("Schedule a tasting", "Confirm per-plate price, taxes and extra-guest rate", "Check dietary options (Jain, vegan, allergens)")),
            ("Photographer & videographer", ("Review recent full albums, not just highlights", "Confirm deliverables and turnaround time", "Agree a shot list for family moments")),
            ("Decorator & florist", ("Share a mood board and get an itemised quote", "Confirm set-up and tear-down timings")),
            ("Music, DJ or band", ("Confirm sound check and a do-not-play list", "Check local permission for loud music and its cut-off time")),
            ("Makeup & attire", ("Book trials well ahead", "Plan alterations at least three weeks before the date")),
        ),
    ),
    "birthday": EventProfile(
        splits={
            "Venue": 20, "Catering & Cake": 35, "Decor & Balloons": 12,
            "Entertainment & Activities": 15, "Photography": 5,
            "Invitations & Return Gifts": 6, CONTINGENCY: 7,
        },
        essential="Catering & Cake", flex="Decor & Balloons", min_per_guest=500, large_event_guests=80,
        timeline=(
            (45, "Set budget, guest list and theme", "Planning"),
            (35, "Book venue or confirm home set-up", "Venue"),
            (28, "Book entertainer, games or activities", "Entertainment"),
            (21, "Order cake and plan the menu", "Catering"),
            (14, "Send invitations and ask for RSVPs", "Guests"),
            (7, "Buy decor and return gifts", "Decor"),
            (3, "Confirm headcount with caterer and vendors", "Vendors"),
            (1, "Set up decor and prepare the schedule", "Logistics"),
            (0, "Event day: cake cutting, games, photos", "Event day"),
            (-3, "Send thank-you messages and share photos", "After event"),
        ),
        vendors=(
            ("Venue or party hall", ("Confirm capacity, timing and decoration rules", "Ask about outside food and cake policy")),
            ("Caterer or bakery", ("Confirm allergens and dietary needs", "Agree cake design and delivery time")),
            ("Decorator", ("Get an itemised theme quote", "Confirm set-up time before guests arrive")),
            ("Entertainer", ("Check age suitability and references", "Confirm equipment and duration")),
            ("Photographer", ("Agree hours and number of edited photos", "Confirm how photos will be shared")),
        ),
    ),
    "community": EventProfile(
        splits={
            "Venue & Permits": 20, "Food & Refreshments": 30, "Sound, AV & Stage": 15,
            "Decor & Signage": 8, "Marketing & Printing": 8, "Volunteers & Safety": 7, CONTINGENCY: 12,
        },
        essential="Food & Refreshments", flex="Decor & Signage", min_per_guest=150, large_event_guests=200,
        timeline=(
            (60, "Define purpose, budget and organising committee", "Planning"),
            (50, "Secure venue and local permissions", "Venue"),
            (40, "Recruit volunteers and assign roles", "Volunteers"),
            (30, "Book sound, stage and refreshments", "Vendors"),
            (21, "Launch publicity: posters, WhatsApp and social posts", "Marketing"),
            (14, "Confirm speakers or performers and the programme", "Programme"),
            (7, "Brief volunteers; arrange first aid and crowd plan", "Safety"),
            (1, "Site check, sound check and signage set-up", "Logistics"),
            (0, "Event day: run the programme and manage the crowd", "Event day"),
            (-5, "Share thanks, photos and an expense summary", "After event"),
        ),
        vendors=(
            ("Venue & permissions", ("Confirm permission from the local authority or society", "Check capacity, parking and noise limits")),
            ("Food & refreshments", ("Confirm quantities against the headcount", "Plan waste disposal and drinking water")),
            ("Sound & AV", ("Test microphones and power backup", "Confirm set-up and tear-down times")),
            ("Safety & first aid", ("Mark exits and keep a first-aid kit", "Share emergency contacts with volunteers")),
            ("Volunteers", ("Assign a lead per area", "Give every volunteer a written schedule")),
        ),
    ),
}


def _shift(splits: dict[str, int], source: str, target: str, points: int) -> int:
    """Move up to ``points`` percentage points between categories; returns points moved."""
    moved = min(points, max(0, splits[source] - 1))
    splits[source] -= moved
    splits[target] += moved
    return moved


def adjusted_splits(
    request: PlanRequest, days_until: int
) -> tuple[dict[str, int], list[str]]:
    """Apply context rules to the base split and explain each change.

    Rules: a tight per-guest budget protects the essential category; very large guest
    lists and short notice both grow the contingency pot.
    """
    profile = PROFILES[request.event_type]
    splits = dict(profile.splits)
    notes: list[str] = []

    if request.budget / request.guest_count < profile.min_per_guest:
        if _shift(splits, profile.flex, profile.essential, 5):
            notes.append(
                f"Budget per guest is tight, so 5 points moved from {profile.flex} to {profile.essential}."
            )
        else:  # pragma: no cover - defensive, flex is never 1% in the base splits
            notes.append("Budget per guest is tight; consider reducing the guest list.")
    if request.guest_count >= profile.large_event_guests:
        if _shift(splits, profile.flex, CONTINGENCY, 2):
            notes.append("Large guest list: contingency raised by 2 points for crowd and logistics surprises.")
    if days_until < SHORT_NOTICE_DAYS:
        if _shift(splits, profile.flex, CONTINGENCY, 3):
            notes.append("Short notice: contingency raised by 3 points to cover rush fees.")
    return splits, notes


def allocate_budget(budget: int, splits: dict[str, int]) -> list[BudgetLine]:
    """Split ``budget`` by whole percentages so the amounts add up exactly (largest remainder)."""
    if sum(splits.values()) != 100:
        raise ValueError("Budget percentages must total 100.")
    base = {name: budget * pct // 100 for name, pct in splits.items()}
    remainders = sorted(splits, key=lambda n: (budget * splits[n]) % 100, reverse=True)
    for name in remainders[: budget - sum(base.values())]:
        base[name] += 1
    return [BudgetLine(category=n, percent=splits[n], amount=base[n]) for n in splits]


def build_timeline(request: PlanRequest, today: date) -> tuple[list[Milestone], bool]:
    """Create dated milestones. Offsets shrink proportionally when there is little lead time.

    Returns ``(milestones, compressed)`` where ``compressed`` means the ideal lead time
    did not fit and tasks were squeezed (nothing is dated before ``today``).
    """
    profile = PROFILES[request.event_type]
    days_until = (request.event_date - today).days
    longest = max(offset for offset, _, _ in profile.timeline)
    scale = min(1.0, days_until / longest)
    milestones: list[Milestone] = []
    for offset, task, category in profile.timeline:
        if offset >= 0:
            due = request.event_date - timedelta(days=round(offset * scale))
        else:
            due = request.event_date + timedelta(days=-offset)
        due = max(due, today)
        milestones.append(
            Milestone(due_date=due, days_from_today=(due - today).days, task=task, category=category)
        )
    milestones.sort(key=lambda m: m.due_date)
    return milestones, scale < 1.0


def build_vendor_checklist(event_type: str) -> list[VendorGroup]:
    """Baseline vendor questions for the event type."""
    return [VendorGroup(vendor=v, items=list(items)) for v, items in PROFILES[event_type].vendors]


def build_core_plan(request: PlanRequest, today: date) -> CorePlan:
    """Compute the full non-AI plan, validating the date window."""
    days_until = (request.event_date - today).days
    if days_until < 0:
        raise PlanInputError("event_date", "The event date cannot be in the past.")
    if days_until > MAX_DAYS_AHEAD:
        raise PlanInputError("event_date", "Please choose a date within the next three years.")

    splits, warnings = adjusted_splits(request, days_until)
    milestones, compressed = build_timeline(request, today)
    if compressed:
        warnings.append(
            f"Only {days_until} day(s) to go: the timeline was compressed and early tasks are due now. "
            "Book venue and caterer first."
        )
    return CorePlan(
        days_until=days_until,
        per_guest=request.budget // request.guest_count,
        budget_lines=allocate_budget(request.budget, splits),
        milestones=milestones,
        vendor_checklist=build_vendor_checklist(request.event_type),
        warnings=warnings,
    )
