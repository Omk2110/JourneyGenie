"""
Budget Optimization Agent -- selects optimal options within budget constraints.
Uses a scoring function combining rating, price, and preferences.
"""

from __future__ import annotations
import logging
from backend.agents.state import TravelPlannerState

logger = logging.getLogger(__name__)


async def budget_optimization_agent(state: TravelPlannerState) -> dict:
    """
    Optimize selections to fit within budget.
    Scores options and selects the best combination.
    """
    budget = state.get("budget", 1000)
    days = state.get("days", 3)
    people = state.get("people", 1)
    search_results = state.get("search_results", {})
    planning_strategy = state.get("planning_strategy", {})
    group_type = state.get("group_type", "solo")

    logger.info(f"[BUDGET] Budget Agent: Optimizing for ₹{budget} budget")

    # ── Get budget allocation from planning strategy ──────────
    allocation = planning_strategy.get("daily_budget_allocation", {
        "accommodation_pct": 35,
        "food_pct": 25,
        "activities_pct": 20,
        "transport_pct": 15,
        "misc_pct": 5,
    })

    # Calculate budget per category
    budget_per_category = {
        "accommodation": budget * allocation.get("accommodation_pct", 35) / 100,
        "food": budget * allocation.get("food_pct", 25) / 100,
        "activities": budget * allocation.get("activities_pct", 20) / 100,
        "transport": budget * allocation.get("transport_pct", 15) / 100,
        "miscellaneous": budget * allocation.get("misc_pct", 5) / 100,
    }

    # ── Select optimal hotel ─────────────────────────────────
    hotels = search_results.get("hotels", [])
    max_nightly = budget_per_category["accommodation"] / max(days, 1)
    selected_hotel = _select_best_hotel(hotels, max_nightly, group_type)

    # ── Select optimal attractions ────────────────────────────
    attractions = search_results.get("attractions", [])
    max_activities_budget = budget_per_category["activities"]
    selected_attractions = _select_best_attractions(attractions, max_activities_budget, days, people)

    # ── Select restaurants ────────────────────────────────────
    restaurants = search_results.get("restaurants", [])
    food_budget_per_day = budget_per_category["food"] / max(days, 1) / max(people, 1)
    selected_restaurants = _select_best_restaurants(restaurants, food_budget_per_day)

    # ── Select flights ────────────────────────────────────────
    flights = search_results.get("flights", [])
    selected_flight = _select_best_flight(flights, budget_per_category["transport"])

    # ── Calculate totals ──────────────────────────────────────
    hotel_cost = (selected_hotel.get("price_per_night", 0) * days) if selected_hotel else 0
    activity_cost = sum(a.get("price", 0) for a in selected_attractions) * people
    food_cost = food_budget_per_day * days * people
    flight_cost = selected_flight.get("total_price", 0) if selected_flight else 0
    transport_cost = flight_cost + (budget_per_category["transport"] * 0.3)  # Local transport estimate
    misc_cost = budget_per_category["miscellaneous"]
    total_estimated = hotel_cost + activity_cost + food_cost + transport_cost + misc_cost

    budget_breakdown = {
        "accommodation": round(hotel_cost, 2),
        "transport": round(transport_cost, 2),
        "food": round(food_cost, 2),
        "activities": round(activity_cost, 2),
        "miscellaneous": round(misc_cost, 2),
        "total_estimated": round(total_estimated, 2),
        "total_budget": budget,
        "remaining": round(budget - total_estimated, 2),
    }

    optimized_plan = {
        "hotel": selected_hotel,
        "attractions": selected_attractions,
        "restaurants": selected_restaurants,
        "flight": selected_flight,
        "daily_food_budget": round(food_budget_per_day, 2),
    }

    logger.info(
        f"[BUDGET] Budget Agent: Total estimated ₹{total_estimated:.0f} / ₹{budget} budget "
        f"(₹{budget - total_estimated:.0f} remaining)"
    )

    return {
        "optimized_plan": optimized_plan,
        "budget_breakdown": budget_breakdown,
        "agent_logs": state.get("agent_logs", []) + [
            f"Budget: Estimated ₹{total_estimated:.0f}/{budget} "
            f"(Hotel: ₹{hotel_cost:.0f}, Activities: ₹{activity_cost:.0f}, "
            f"Food: ₹{food_cost:.0f}, Transport: ₹{transport_cost:.0f})"
        ],
    }


def _score_option(item: dict, max_price: float) -> float:
    """
    Score an option using composite metric:
    0.4 * rating_norm + 0.4 * price_efficiency + 0.2 * data_quality
    """
    rating = item.get("rating", 0)
    price = item.get("price", item.get("price_per_night", 0))

    rating_norm = min(rating / 5.0, 1.0) if rating else 0.3
    price_norm = 1.0 - min(price / max(max_price, 1), 1.0) if price > 0 else 0.5
    data_quality = 0.8 if item.get("source") != "fallback" else 0.5

    return 0.4 * rating_norm + 0.4 * price_norm + 0.2 * data_quality


def _select_best_hotel(hotels: list[dict], max_nightly: float, group_type: str) -> dict | None:
    """Select the best hotel within budget."""
    if not hotels:
        return None

    # Filter to affordable options
    affordable = [h for h in hotels if h.get("price_per_night", 0) <= max_nightly * 1.1]
    if not affordable:
        # Take the cheapest option if nothing fits
        affordable = sorted(hotels, key=lambda h: h.get("price_per_night", 999))[:3]

    # Score and select
    scored = [(h, _score_option(h, max_nightly)) for h in affordable]
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[0][0] if scored else hotels[0]


def _select_best_attractions(
    attractions: list[dict], total_budget: float, days: int, people: int
) -> list[dict]:
    """Select attractions using a knapsack-like approach to maximize value within budget."""
    if not attractions:
        return []

    per_person_budget = total_budget / max(people, 1)

    # Score all attractions
    scored = []
    for a in attractions:
        price = a.get("price", 0)
        score = _score_option(a, per_person_budget / max(days, 1))
        scored.append((a, score, price))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Greedy knapsack: select until budget is exhausted
    selected = []
    remaining_budget = per_person_budget
    target_count = days * 3  # ~3 attractions per day

    for attraction, score, price in scored:
        if len(selected) >= target_count:
            break
        if price <= remaining_budget or price == 0:
            selected.append(attraction)
            remaining_budget -= price

    return selected


def _select_best_restaurants(restaurants: list[dict], daily_budget_pp: float) -> list[dict]:
    """Select diverse restaurants within daily per-person food budget."""
    if not restaurants:
        return []

    # Score and sort
    scored = [(r, _score_option(r, daily_budget_pp * 2)) for r in restaurants]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [r for r, _ in scored[:6]]


def _select_best_flight(flights: list[dict], transport_budget: float) -> dict | None:
    """Select the best value flight."""
    if not flights:
        return None

    # Score flights by price and stops
    def flight_score(f):
        price = f.get("total_price", f.get("price_per_person", 999))
        stops = f.get("stops", 0)
        price_score = 1.0 - min(price / max(transport_budget, 1), 1.0)
        stop_penalty = stops * 0.15
        return price_score - stop_penalty

    scored = [(f, flight_score(f)) for f in flights]
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[0][0] if scored else None
