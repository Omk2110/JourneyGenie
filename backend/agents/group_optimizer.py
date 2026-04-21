"""
Group Optimization Agent -- classifies group type and adjusts preferences.
"""

from __future__ import annotations
import logging
from backend.agents.state import TravelPlannerState

logger = logging.getLogger(__name__)


async def group_optimization_agent(state: TravelPlannerState) -> dict:
    """
    Classify the travel group and adjust search/planning parameters accordingly.
    Deterministic logic -- no LLM call needed.
    """
    people = state.get("people", 1)
    preferences = state.get("preferences", [])
    planning_strategy = state.get("planning_strategy", {})

    # ── Classify Group Type ───────────────────────────────────
    if people == 1:
        group_type = "solo"
    elif people == 2:
        # Default to couple; preferences can override
        group_type = "couple"
        if any(p in preferences for p in ["family", "kids", "children"]):
            group_type = "family"
    elif people <= 4:
        if any(p in preferences for p in ["family", "kids", "children"]):
            group_type = "family"
        else:
            group_type = "friends"
    else:
        group_type = "family" if any(p in preferences for p in ["family", "kids", "children"]) else "friends"

    # ── Group-Specific Adjustments ────────────────────────────
    adjustments = _get_group_adjustments(group_type, people, planning_strategy)

    logger.info(f"[GROUP] Group Agent: Classified as '{group_type}' ({people} people)")

    return {
        "group_type": group_type,
        "group_adjustments": adjustments,
        "agent_logs": state.get("agent_logs", []) + [
            f"Group Optimizer: Classified as '{group_type}' group ({people} travelers)"
        ],
    }


def _get_group_adjustments(group_type: str, people: int, strategy: dict) -> dict:
    """Generate group-specific adjustments for accommodation, transport, and activities."""

    base_adjustments = {
        "solo": {
            "accommodation": {
                "type_preference": ["hostel", "boutique_hotel", "apartment"],
                "room_config": "single",
                "rooms_needed": 1,
            },
            "transport": {
                "mode_preference": ["public_transit", "walking", "bike"],
                "sharing": False,
            },
            "activities": {
                "style": "flexible",
                "social_activities": True,
                "group_tours": True,
                "pace": "intensive",
                "avoid": [],
            },
            "dining": {
                "style": "street_food_and_casual",
                "group_bookings": False,
            },
        },
        "couple": {
            "accommodation": {
                "type_preference": ["boutique_hotel", "hotel", "resort"],
                "room_config": "double",
                "rooms_needed": 1,
            },
            "transport": {
                "mode_preference": ["taxi", "rental_car", "public_transit"],
                "sharing": True,
            },
            "activities": {
                "style": "romantic",
                "social_activities": False,
                "group_tours": False,
                "pace": "moderate",
                "avoid": [],
                "prefer": ["scenic_views", "fine_dining", "private_tours"],
            },
            "dining": {
                "style": "fine_dining_and_casual",
                "group_bookings": False,
            },
        },
        "family": {
            "accommodation": {
                "type_preference": ["apartment", "family_hotel", "resort"],
                "room_config": "family",
                "rooms_needed": max(1, (people + 1) // 2),
            },
            "transport": {
                "mode_preference": ["rental_car", "taxi", "private_transfer"],
                "sharing": True,
            },
            "activities": {
                "style": "family_friendly",
                "social_activities": False,
                "group_tours": True,
                "pace": "relaxed",
                "avoid": ["nightlife", "extreme_sports"],
                "prefer": ["parks", "museums", "amusement", "beach"],
            },
            "dining": {
                "style": "family_restaurants",
                "group_bookings": True,
            },
        },
        "friends": {
            "accommodation": {
                "type_preference": ["hostel", "apartment", "hotel"],
                "room_config": "shared",
                "rooms_needed": max(1, (people + 1) // 2),
            },
            "transport": {
                "mode_preference": ["public_transit", "shared_taxi", "bus"],
                "sharing": True,
            },
            "activities": {
                "style": "adventure",
                "social_activities": True,
                "group_tours": True,
                "pace": "intensive",
                "avoid": [],
                "prefer": ["nightlife", "adventure", "group_activities", "food_tours"],
            },
            "dining": {
                "style": "mixed_group_dining",
                "group_bookings": True,
            },
        },
    }

    return base_adjustments.get(group_type, base_adjustments["friends"])
