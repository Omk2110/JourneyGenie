"""
Itinerary Generator Agent -- creates a day-wise itinerary.
Clusters nearby places and balances activity intensity.
"""

from __future__ import annotations
import json
import logging
from backend.agents.state import TravelPlannerState
from backend.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

ITINERARY_SYSTEM_PROMPT = """You are an expert itinerary planner. Given a list of selected attractions/activities, restaurants, and trip details, create an optimal day-by-day itinerary.

Rules:
1. Cluster nearby places together on the same day
2. Minimize travel time between consecutive activities
3. Balance activity intensity -- don't pack too many high-energy activities in one day
4. Include meal breaks (breakfast, lunch, dinner)
5. Start each day around 09:00 and end by 21:00
6. Leave buffer time for travel between locations
7. Include free/rest time

Output a JSON array where each element is a day:
[
  {
    "day": 1,
    "theme": "Historical & Cultural Exploration",
    "activities": [
      {
        "name": "Place Name",
        "time": "09:00 - 10:30",
        "duration_minutes": 90,
        "category": "attraction",
        "description": "Brief description of the activity",
        "estimated_cost": 25.0,
        "latitude": 48.8584,
        "longitude": 2.2945
      }
    ]
  }
]

Include meal activities (breakfast, lunch, dinner) with restaurant suggestions.
Return ONLY the JSON array, no other text or markdown."""


async def itinerary_generator_agent(state: TravelPlannerState) -> dict:
    """
    Create a day-wise itinerary from optimized plan.
    Uses LLM for intelligent scheduling and clustering.
    """
    days = state.get("days", 3)
    destination = state.get("destination", "")
    optimized_plan = state.get("optimized_plan", {})
    preferences = state.get("preferences", [])
    group_type = state.get("group_type", "solo")
    constraints = state.get("constraints", {})
    validation_feedback = state.get("validation_feedback", "")

    attractions = optimized_plan.get("attractions", [])
    restaurants = optimized_plan.get("restaurants", [])
    hotel = optimized_plan.get("hotel", {})

    logger.info(f"[ITIN] Itinerary Agent: Creating {days}-day itinerary for {destination}")

    # Build context for LLM
    attractions_text = "\n".join(
        f"- {a.get('name', 'Unknown')} (Rating: {a.get('rating', 'N/A')}, "
        f"Cost: ${a.get('price', 0)}, Lat: {a.get('latitude', 0)}, Lng: {a.get('longitude', 0)})"
        for a in attractions
    )

    restaurants_text = "\n".join(
        f"- {r.get('name', 'Unknown')} (Rating: {r.get('rating', 'N/A')}, Cost: ${r.get('price', 0)})"
        for r in restaurants
    )

    reiteration_text = ""
    if validation_feedback:
        logger.warning(f"[ITIN] Itinerary Agent processing Re-iteration feedback: {validation_feedback}")
        reiteration_text = f"""
!!! CRITICAL REITERATION FEEDBACK !!!
The previous itinerary you generated was REJECTED by the validator for the following reasons:
{validation_feedback}

You MUST fix these issues in this new generation. Focus on what the user wants in their travel plan and strictly distribute activities evenly among all the days.
"""

    user_prompt = f"""Create a {days}-day itinerary for {destination}.
{reiteration_text}
Group Type: {group_type}
Preferences: {', '.join(preferences) if preferences else 'general'}
Max activities per day: {constraints.get('max_activities_per_day', 4)}
Daily start: {constraints.get('preferred_start_time', '09:00')}
Daily end: {constraints.get('preferred_end_time', '21:00')}

Hotel: {hotel.get('name', 'Central Hotel')} (at {hotel.get('address', destination)})

Available Attractions:
{attractions_text or 'Use popular attractions in ' + destination}

Available Restaurants:
{restaurants_text or 'Use popular restaurants in ' + destination}

Remember: Cluster nearby places, include meals, and balance the intensity of each day."""

    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=ITINERARY_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = await llm.ainvoke(messages)

        content = response.content
        if isinstance(content, list):
            content = "".join([p.get("text", "") for p in content if isinstance(p, dict)])
        content = str(content).strip()
        # Remove markdown code fences
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("json"):
            content = content[4:].strip()

        itinerary = json.loads(content)

    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Itinerary LLM parse error: {e}, using algorithmic fallback")
        itinerary = _build_fallback_itinerary(days, attractions, restaurants, destination, constraints)

    # Ensure coordinates are present
    itinerary = _enrich_with_coordinates(itinerary, attractions, restaurants)

    logger.info(f"[ITIN] Itinerary Agent: Generated {len(itinerary)} days")

    return {
        "itinerary": itinerary,
        "agent_logs": state.get("agent_logs", []) + [
            f"Itinerary: Created {len(itinerary)}-day plan with {sum(len(d.get('activities', [])) for d in itinerary)} activities"
        ],
    }


def _build_fallback_itinerary(
    days: int,
    attractions: list[dict],
    restaurants: list[dict],
    destination: str,
    constraints: dict,
) -> list[dict]:
    """Build a reasonable itinerary algorithmically when LLM fails."""
    max_per_day = constraints.get("max_activities_per_day", 4)
    itinerary = []

    # Distribute attractions across days
    attraction_idx = 0
    restaurant_idx = 0

    themes = [
        "Cultural Exploration", "Historical Discovery", "Local Experience",
        "Nature & Scenic", "Art & Architecture", "Food & Markets",
        "Adventure Day", "Relaxation Day",
    ]

    for day in range(1, days + 1):
        activities = []
        time_slots = ["09:00 - 10:30", "11:00 - 12:30", "14:00 - 15:30",
                       "16:00 - 17:30", "19:00 - 20:30"]

        # Breakfast
        activities.append({
            "name": f"Breakfast at hotel",
            "time": "08:00 - 08:45",
            "duration_minutes": 45,
            "category": "meal",
            "description": "Start the day with a good breakfast",
            "estimated_cost": 15.0,
            "latitude": 0.0,
            "longitude": 0.0,
        })

        # Morning + Afternoon attractions
        for slot_idx in range(min(max_per_day, len(time_slots) - 1)):
            if attraction_idx < len(attractions):
                att = attractions[attraction_idx]
                activities.append({
                    "name": att.get("name", f"Activity {slot_idx + 1}"),
                    "time": time_slots[slot_idx],
                    "duration_minutes": 90,
                    "category": att.get("category", "attraction"),
                    "description": att.get("description", f"Visit {att.get('name', 'attraction')}"),
                    "estimated_cost": att.get("price", 0),
                    "latitude": att.get("latitude", 0.0),
                    "longitude": att.get("longitude", 0.0),
                })
                attraction_idx += 1

            if slot_idx == 1:  # Add lunch
                rest = restaurants[restaurant_idx % max(len(restaurants), 1)] if restaurants else {}
                activities.append({
                    "name": rest.get("name", f"Lunch in {destination}"),
                    "time": "12:30 - 13:30",
                    "duration_minutes": 60,
                    "category": "meal",
                    "description": "Lunch break",
                    "estimated_cost": rest.get("price", 20),
                    "latitude": rest.get("latitude", 0.0),
                    "longitude": rest.get("longitude", 0.0),
                })
                restaurant_idx += 1

        # Dinner
        rest = restaurants[restaurant_idx % max(len(restaurants), 1)] if restaurants else {}
        activities.append({
            "name": rest.get("name", f"Dinner in {destination}"),
            "time": "19:30 - 21:00",
            "duration_minutes": 90,
            "category": "meal",
            "description": "Dinner",
            "estimated_cost": rest.get("price", 30),
            "latitude": rest.get("latitude", 0.0),
            "longitude": rest.get("longitude", 0.0),
        })
        restaurant_idx += 1

        # Sort by time
        activities.sort(key=lambda a: a.get("time", ""))

        itinerary.append({
            "day": day,
            "theme": themes[(day - 1) % len(themes)],
            "activities": activities,
        })

    return itinerary


def _enrich_with_coordinates(
    itinerary: list[dict],
    attractions: list[dict],
    restaurants: list[dict],
) -> list[dict]:
    """Ensure all itinerary activities have coordinates from search results."""
    # Build lookup by name
    coords_lookup = {}
    for item in attractions + restaurants:
        name = item.get("name", "").lower()
        if name and (item.get("latitude") or item.get("longitude")):
            coords_lookup[name] = {
                "latitude": item.get("latitude", 0),
                "longitude": item.get("longitude", 0),
            }

    for day in itinerary:
        for activity in day.get("activities", []):
            if not activity.get("latitude") and not activity.get("longitude"):
                name_lower = activity.get("name", "").lower()
                if name_lower in coords_lookup:
                    activity["latitude"] = coords_lookup[name_lower]["latitude"]
                    activity["longitude"] = coords_lookup[name_lower]["longitude"]

    return itinerary
