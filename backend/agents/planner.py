"""
Planner Agent -- parses user input and creates a structured planning strategy.
First node in the agent graph.
"""

from __future__ import annotations
import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from backend.llm import get_llm
from backend.agents.state import TravelPlannerState

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are an expert travel planner agent. Your job is to analyze the user's travel request and create a structured planning strategy.

Given the user's inputs, you must output a JSON object with the following structure:
{
    "destination_analysis": {
        "city": "<city name>",
        "country": "<country>",
        "region": "<region/continent>",
        "popular_areas": ["<area1>", "<area2>"]
    },
    "trip_profile": {
        "pace": "relaxed|moderate|intense",
        "focus_areas": ["<focus1>", "<focus2>"],
        "budget_tier": "budget|mid-range|premium|luxury"
    },
    "search_priorities": {
        "accommodation_type": "<hotel|hostel|apartment|resort>",
        "transport_mode": "<public|taxi|rental|walking>",
        "dining_style": "<street_food|casual|fine_dining|mixed>",
        "activity_types": ["<type1>", "<type2>"]
    },
    "daily_budget_allocation": {
        "accommodation_pct": <0-100>,
        "food_pct": <0-100>,
        "activities_pct": <0-100>,
        "transport_pct": <0-100>,
        "misc_pct": <0-100>
    },
    "constraints": {
        "max_activities_per_day": <3-6>,
        "preferred_start_time": "<HH:MM>",
        "preferred_end_time": "<HH:MM>"
    }
}

IMPORTANT: Return ONLY the JSON object, no markdown formatting or extra text."""


async def planner_agent(state: TravelPlannerState) -> dict:
    """
    Parse user intent and create a structured planning strategy.
    """
    logger.info(f"[MAP] Planner Agent: Planning trip to {state.get('destination', 'unknown')}")

    destination = state.get("destination", "")
    days = state.get("days", 3)
    budget = state.get("budget", 1000)
    people = state.get("people", 1)
    preferences = state.get("preferences", [])

    # Calculate per-person-per-day budget
    daily_budget = budget / max(days, 1)
    per_person_daily = daily_budget / max(people, 1)

    # Determine budget tier (INR thresholds)
    if per_person_daily < 4000:
        budget_tier = "budget"
    elif per_person_daily < 12000:
        budget_tier = "mid-range"
    elif per_person_daily < 25000:
        budget_tier = "premium"
    else:
        budget_tier = "luxury"

    user_prompt = f"""Plan a trip with these details:
- Destination: {destination}
- Duration: {days} days
- Total Budget: ₹{budget} INR
- Number of Travelers: {people}
- Per Person Per Day Budget: ₹{per_person_daily:.0f}
- Budget Tier: {budget_tier}
- Preferences: {', '.join(preferences) if preferences else 'general sightseeing'}

Create a detailed planning strategy. All costs should be in Indian Rupees (₹ INR)."""

    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = await llm.ainvoke(messages)

        # Parse JSON from response
        content = response.content.strip()
        # Remove markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        if content.startswith("json"):
            content = content[4:].strip()

        planning_strategy = json.loads(content)

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        planning_strategy = _build_default_strategy(destination, days, budget, people, preferences, budget_tier)
    except Exception as e:
        logger.error(f"Planner Agent LLM error: {e}")
        planning_strategy = _build_default_strategy(destination, days, budget, people, preferences, budget_tier)

    return {
        "planning_strategy": planning_strategy,
        "constraints": planning_strategy.get("constraints", {
            "max_activities_per_day": 4,
            "preferred_start_time": "09:00",
            "preferred_end_time": "21:00",
        }),
        "agent_logs": state.get("agent_logs", []) + [
            f"Planner: Created strategy for {days}-day {budget_tier} trip to {destination}"
        ],
    }


def _build_default_strategy(
    destination: str, days: int, budget: int, people: int,
    preferences: list[str], budget_tier: str
) -> dict:
    """Build a sensible default strategy when LLM fails."""
    # Map preferences to activity types
    activity_map = {
        "adventure": ["hiking", "water_sports", "extreme_sports"],
        "cultural": ["museums", "historical_sites", "local_events"],
        "relaxation": ["spa", "beach", "parks"],
        "food": ["food_tours", "cooking_classes", "local_restaurants"],
        "nightlife": ["bars", "clubs", "night_markets"],
        "nature": ["parks", "nature_reserves", "scenic_viewpoints"],
        "shopping": ["markets", "malls", "boutiques"],
    }
    activity_types = []
    for pref in preferences:
        activity_types.extend(activity_map.get(pref.lower(), ["sightseeing"]))
    if not activity_types:
        activity_types = ["sightseeing", "museums", "local_restaurants"]

    accommodation_map = {
        "budget": "hostel",
        "mid-range": "hotel",
        "premium": "hotel",
        "luxury": "resort",
    }

    return {
        "destination_analysis": {
            "city": destination,
            "country": "",
            "region": "",
            "popular_areas": [],
        },
        "trip_profile": {
            "pace": "moderate",
            "focus_areas": preferences or ["general"],
            "budget_tier": budget_tier,
        },
        "search_priorities": {
            "accommodation_type": accommodation_map.get(budget_tier, "hotel"),
            "transport_mode": "public" if budget_tier in ("budget", "mid-range") else "taxi",
            "dining_style": "mixed",
            "activity_types": activity_types[:5],
        },
        "daily_budget_allocation": {
            "accommodation_pct": 35,
            "food_pct": 25,
            "activities_pct": 20,
            "transport_pct": 15,
            "misc_pct": 5,
        },
        "constraints": {
            "max_activities_per_day": 4,
            "preferred_start_time": "09:00",
            "preferred_end_time": "21:00",
        },
    }
