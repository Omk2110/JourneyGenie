"""
Report Generator Agent -- assembles the final structured output.
Last node in the graph.
"""

from __future__ import annotations
import logging
from backend.agents.state import TravelPlannerState
from backend.config import settings

logger = logging.getLogger(__name__)


async def report_generator_agent(state: TravelPlannerState) -> dict:
    """
    Assemble the final structured JSON output for the frontend.
    Produces the strict output format required.
    """
    logger.info("[REPORT] Report Agent: Generating final output")

    destination = state.get("destination", "")
    days = state.get("days", 3)
    budget = state.get("budget", 1000)
    people = state.get("people", 1)
    group_type = state.get("group_type", "solo")
    budget_breakdown = state.get("budget_breakdown", {})
    itinerary = state.get("itinerary", [])
    map_data = state.get("map_data", [])
    cultural_insights = state.get("cultural_insights", [])
    best_time = state.get("best_time_to_visit", {})
    warnings = state.get("warnings", [])
    optimized_plan = state.get("optimized_plan", {})
    weather_data = state.get("weather_data", {})

    # ── Summary ───────────────────────────────────────────────
    summary = {
        "destination": destination,
        "duration_days": days,
        "group_type": group_type,
        "total_budget": budget,
        "estimated_cost": budget_breakdown.get("total_estimated", 0),
        "people": people,
        "best_time_to_visit": f"{', '.join(best_time.get('months', [])[:3])}",
        "best_time_months": best_time.get("months", []),
        "best_time_reasoning": best_time.get("reasoning", ""),
    }

    # ── Format itinerary ──────────────────────────────────────
    formatted_itinerary = []
    for day_plan in itinerary:
        activities = []
        day_cost = 0.0
        for act in day_plan.get("activities", []):
            cost = act.get("estimated_cost", 0)
            day_cost += cost
            activities.append({
                "name": act.get("name", ""),
                "time": act.get("time", ""),
                "duration_minutes": act.get("duration_minutes", 60),
                "category": act.get("category", ""),
                "description": act.get("description", ""),
                "latitude": act.get("latitude", 0.0),
                "longitude": act.get("longitude", 0.0),
                "estimated_cost": cost,
                "rating": act.get("rating", 0.0),
            })

        formatted_itinerary.append({
            "day": day_plan.get("day", 0),
            "date": day_plan.get("date", ""),
            "theme": day_plan.get("theme", ""),
            "activities": activities,
            "total_cost": round(day_cost, 2),
            "travel_time_minutes": day_plan.get("travel_time_minutes", 0),
        })

    # ── Recommendations ───────────────────────────────────────
    recommendations = []

    hotel = optimized_plan.get("hotel")
    if hotel:
        recommendations.append({
            "title": f"Stay at {hotel.get('name', 'Selected Hotel')}",
            "description": (
                f"₹{hotel.get('price_per_night', 0)}/night, "
                f"Rating: {hotel.get('rating', 'N/A')}/5, "
                f"{hotel.get('description', '')}"
            ),
            "priority": "high",
        })

    flight = optimized_plan.get("flight")
    if flight:
        recommendations.append({
            "title": f"Fly with {flight.get('airline', 'Selected Airline')}",
            "description": (
                f"₹{flight.get('total_price', 0)} total, "
                f"Duration: {flight.get('duration', 'N/A')}, "
                f"Stops: {flight.get('stops', 0)}"
            ),
            "priority": "high",
        })

    # Add weather-based recommendation
    if weather_data:
        temp = weather_data.get("temperature_celsius", 20)
        desc = weather_data.get("description", "")
        if temp > 30:
            recommendations.append({
                "title": "Pack for hot weather",
                "description": f"Expected {temp}°C with {desc}. Bring sunscreen, light clothing, and stay hydrated.",
                "priority": "medium",
            })
        elif temp < 10:
            recommendations.append({
                "title": "Pack warm layers",
                "description": f"Expected {temp}°C with {desc}. Bring warm jackets and layers.",
                "priority": "medium",
            })

    # ── Insights ──────────────────────────────────────────────
    insights = []

    # Budget insight
    remaining = budget_breakdown.get("remaining", 0)
    if remaining > 0:
        insights.append({
            "title": "Budget Buffer",
            "description": f"You have ₹{remaining:.0f} remaining as buffer for unexpected expenses.",
            "category": "budget",
        })
    elif remaining < 0:
        insights.append({
            "title": "Budget Warning",
            "description": f"Estimated cost exceeds budget by ₹{abs(remaining):.0f}. Consider optimizing.",
            "category": "budget",
        })

    # Weather insight
    if weather_data:
        insights.append({
            "title": "Weather Conditions",
            "description": (
                f"{weather_data.get('temperature_celsius', 'N/A')}°C, "
                f"{weather_data.get('description', 'N/A')}. "
                f"Humidity: {weather_data.get('humidity', 'N/A')}%"
            ),
            "category": "weather",
        })

    # Cultural insights
    for ci in cultural_insights[:4]:
        insights.append({
            "title": "Cultural Tip",
            "description": ci,
            "category": "cultural",
        })

    # Best time insight
    if best_time.get("reasoning"):
        insights.append({
            "title": "Best Time to Visit",
            "description": best_time["reasoning"],
            "category": "timing",
        })

    # ── Final Output ──────────────────────────────────────────
    final_output = {
        "summary": summary,
        "budget_breakdown": {
            "accommodation": budget_breakdown.get("accommodation", 0),
            "transport": budget_breakdown.get("transport", 0),
            "food": budget_breakdown.get("food", 0),
            "activities": budget_breakdown.get("activities", 0),
            "miscellaneous": budget_breakdown.get("miscellaneous", 0),
            "total_estimated": budget_breakdown.get("total_estimated", 0),
            "total_budget": budget,
            "remaining": budget_breakdown.get("remaining", 0),
        },
        "itinerary": formatted_itinerary,
        "map_data": [
            {
                "name": mp.get("name", ""),
                "latitude": mp.get("latitude", 0),
                "longitude": mp.get("longitude", 0),
                "day": mp.get("day", 0),
                "order": mp.get("order", 0),
                "category": mp.get("category", ""),
            }
            for mp in map_data
        ],
        "recommendations": recommendations,
        "insights": insights,
        "warnings": warnings,
        "missing_api_keys": settings.get_missing_api_keys(),
    }

    logger.info(f"[REPORT] Report Agent: Final output ready -- {len(formatted_itinerary)} days, {len(map_data)} map points")

    return {
        "final_output": final_output,
        "agent_logs": state.get("agent_logs", []) + [
            f"Report: Generated final output with {len(formatted_itinerary)} days, "
            f"{len(recommendations)} recommendations, {len(insights)} insights"
        ],
    }
