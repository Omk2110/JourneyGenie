"""
Pydantic models for request/response validation and structured data.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


# ── Input Models ──────────────────────────────────────────────


class TravelInput(BaseModel):
    """User input for trip planning."""
    destination: str = Field(..., description="Travel destination city/country")
    days: int = Field(..., ge=1, le=30, description="Number of travel days")
    budget: int = Field(..., ge=1000, description="Total budget in INR (Indian Rupees)")
    people: int = Field(..., ge=1, le=20, description="Number of travelers")
    preferences: list[str] = Field(
        default_factory=list,
        description="Travel preferences: adventure, cultural, relaxation, food, nightlife, nature, shopping"
    )
    start_date: Optional[str] = Field(None, description="Trip start date (YYYY-MM-DD)")
    origin: Optional[str] = Field(None, description="Origin city for flight search")


# ── Internal Models ───────────────────────────────────────────


class SearchResult(BaseModel):
    """A single search result from API tools."""
    name: str
    category: str  # hotel, restaurant, attraction, transport
    price: float = 0.0
    rating: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0
    address: str = ""
    description: str = ""
    image_url: str = ""
    source: str = ""  # Which API provided this


class ItineraryActivity(BaseModel):
    """A single activity within a day."""
    name: str
    time: str  # e.g., "09:00 - 10:30"
    duration_minutes: int = 60
    category: str = ""
    description: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    estimated_cost: float = 0.0
    rating: float = 0.0


class ItineraryDay(BaseModel):
    """One day of the itinerary."""
    day: int
    date: str = ""
    theme: str = ""
    activities: list[ItineraryActivity] = Field(default_factory=list)
    total_cost: float = 0.0
    travel_time_minutes: int = 0


class BudgetBreakdown(BaseModel):
    """Budget allocation across categories."""
    accommodation: float = 0.0
    transport: float = 0.0
    food: float = 0.0
    activities: float = 0.0
    miscellaneous: float = 0.0
    total_estimated: float = 0.0
    total_budget: float = 0.0
    remaining: float = 0.0


class MapPoint(BaseModel):
    """A point on the map with day grouping."""
    name: str
    latitude: float
    longitude: float
    day: int
    order: int  # Order within the day
    category: str = ""


class Insight(BaseModel):
    """An AI reasoning insight."""
    title: str
    description: str
    category: str = ""  # weather, cultural, budget, timing


class Recommendation(BaseModel):
    """A recommendation from the system."""
    title: str
    description: str
    priority: str = "medium"  # low, medium, high


# ── Output Models ─────────────────────────────────────────────


class TripSummary(BaseModel):
    """High-level summary of the planned trip."""
    destination: str
    duration_days: int
    group_type: str
    total_budget: float
    estimated_cost: float
    people: int
    best_time_to_visit: str = ""
    best_time_months: list[str] = Field(default_factory=list)
    best_time_reasoning: str = ""


class FinalOutput(BaseModel):
    """The complete structured output from the planner."""
    summary: TripSummary
    budget_breakdown: BudgetBreakdown
    itinerary: list[ItineraryDay] = Field(default_factory=list)
    map_data: list[MapPoint] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    insights: list[Insight] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    missing_api_keys: list[str] = Field(default_factory=list)
