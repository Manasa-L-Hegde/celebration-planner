"""Pydantic models: validated request, plan sections and AI insight schema."""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .security import clean_text, looks_like_injection

EventType = Literal["wedding", "birthday", "community"]


class PlanRequest(BaseModel):
    """User input for a plan. Unknown fields are rejected."""

    model_config = ConfigDict(extra="forbid")

    event_type: EventType
    title: str = Field(min_length=1, max_length=80)
    guest_count: int = Field(ge=1, le=2000)
    budget: int = Field(ge=1_000, le=100_000_000, description="Total budget in INR")
    event_date: date
    city: str = Field(min_length=1, max_length=60)
    preferences: str = Field(default="", max_length=500)

    @field_validator("title", "city", "preferences", mode="before")
    @classmethod
    def _clean_and_screen(cls, value: object) -> object:
        if not isinstance(value, str):
            raise ValueError("Must be text.")
        cleaned = clean_text(value)
        if looks_like_injection(cleaned):
            raise ValueError("Please describe the event only; instructions to the assistant are not allowed.")
        return cleaned


class BudgetLine(BaseModel):
    category: str
    percent: int
    amount: int


class Milestone(BaseModel):
    due_date: date
    days_from_today: int
    task: str
    category: str


class VendorGroup(BaseModel):
    vendor: str
    items: list[str]


class CorePlan(BaseModel):
    """Everything computed deterministically, without the LLM."""

    days_until: int
    per_guest: int
    budget_lines: list[BudgetLine]
    milestones: list[Milestone]
    vendor_checklist: list[VendorGroup]
    warnings: list[str]


class Idea(BaseModel):
    title: str
    description: str


class ChecklistExtra(BaseModel):
    category: str
    item: str


class AIInsights(BaseModel):
    """Structured output requested from Gemini (also used for the offline fallback)."""

    summary: str
    ideas: list[Idea]
    checklist_extras: list[ChecklistExtra]
    saving_tips: list[str]


class PlanResult(BaseModel):
    """Full API response."""

    title: str
    event_type: EventType
    event_date: date
    city: str
    guest_count: int
    budget: int
    days_until: int
    per_guest: int
    budget_lines: list[BudgetLine]
    milestones: list[Milestone]
    vendor_checklist: list[VendorGroup]
    warnings: list[str]
    insights: AIInsights
    ai_source: Literal["gemini", "fallback"]
