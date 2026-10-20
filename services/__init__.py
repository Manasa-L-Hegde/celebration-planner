"""Services layer for Celebration & Event Planner.

This package organizes domain and external service integrations into clear,
reusable modules:
- planner_service: deterministic budget allocation, timeline milestones, and vendor checklists.
- ai_service: Gemini GenAI integration, caching, output sanitization, and offline fallbacks.
"""
from __future__ import annotations

from .ai_service import GeminiProvider, InsightsProvider, InsightsService
from .planner_service import create_plan

__all__ = [
    "create_plan",
    "GeminiProvider",
    "InsightsProvider",
    "InsightsService",
]
