"""
Shared state schema for the LangGraph travel planner.
All agents read from and write to this state object.
"""

from __future__ import annotations
from typing import TypedDict, Any


class TravelPlannerState(TypedDict, total=False):
    """
    Shared state passed between all agents in the graph.
    Each agent reads what it needs and writes its outputs.
    """
    # ── User Inputs ───────────────────────────────────────────
    destination: str
    days: int
    budget: int
    people: int
    preferences: list[str]
    start_date: str
    origin: str

    # ── Planner Output ────────────────────────────────────────
    planning_strategy: dict[str, Any]

    # ── Group Optimization Output ─────────────────────────────
    group_type: str  # solo, couple, family, friends
    group_adjustments: dict[str, Any]

    # ── Search Results ────────────────────────────────────────
    search_results: dict[str, Any]  # hotels, attractions, restaurants, flights

    # ── Budget Optimization Output ────────────────────────────
    optimized_plan: dict[str, Any]
    budget_breakdown: dict[str, Any]

    # ── Itinerary Output ──────────────────────────────────────
    itinerary: list[dict[str, Any]]

    # ── Map Data ──────────────────────────────────────────────
    map_data: list[dict[str, Any]]
    destination_coords: dict[str, float]

    # ── Context Agent Output ──────────────────────────────────
    weather_data: dict[str, Any]
    cultural_insights: list[str]
    best_time_to_visit: dict[str, Any]

    # ── Validator Output ──────────────────────────────────────
    validation_result: dict[str, Any]
    validation_passed: bool
    validation_feedback: str
    retry_count: int

    # ── Final Output ──────────────────────────────────────────
    final_output: dict[str, Any]

    # ── Meta ──────────────────────────────────────────────────
    errors: list[str]
    warnings: list[str]
    agent_logs: list[str]
    constraints: dict[str, Any]
