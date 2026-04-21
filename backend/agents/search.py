"""
Search Agent -- tool-using agent that fetches real-time data from APIs.
Parallelizes all API calls for performance.
"""

from __future__ import annotations
import asyncio
import logging
from backend.agents.state import TravelPlannerState
from backend.tools.google_places import search_places
from backend.tools.hotels import search_hotels
from backend.tools.flights import search_flights
from backend.tools.weather import get_weather
from backend.tools.geocoding import geocode_place

logger = logging.getLogger(__name__)


async def search_agent(state: TravelPlannerState) -> dict:
    """
    Parallel search across all data sources: places, hotels, flights, weather.
    Uses asyncio.gather for maximum performance.
    """
    destination = state.get("destination", "")
    days = state.get("days", 3)
    people = state.get("people", 1)
    preferences = state.get("preferences", [])
    origin = state.get("origin", "")
    start_date = state.get("start_date", "")
    planning_strategy = state.get("planning_strategy", {})
    group_adjustments = state.get("group_adjustments", {})

    logger.info(f"[SEARCH] Search Agent: Searching data for {destination}")

    # ── Build search queries from strategy ────────────────────
    activity_types = (
        planning_strategy.get("search_priorities", {}).get("activity_types", [])
        or ["attractions", "restaurants", "sightseeing"]
    )

    # ── Parallel API calls ────────────────────────────────────
    search_tasks = [
        # Attractions and places
        search_places(destination, destination, "attraction", 10),
        # Restaurants
        search_places(f"best restaurants in {destination}", destination, "restaurant", 8),
        # Hotels
        search_hotels(destination, adults=people, max_results=8),
        # Weather
        get_weather(destination),
        # Geocode destination
        geocode_place(destination),
    ]

    # Add flight search if origin is specified
    if origin:
        search_tasks.append(
            search_flights(origin, destination, start_date or "2026-05-01", people)
        )

    # Execute all searches in parallel
    results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # ── Process results ───────────────────────────────────────
    attractions = results[0] if not isinstance(results[0], Exception) else []
    restaurants = results[1] if not isinstance(results[1], Exception) else []
    hotels = results[2] if not isinstance(results[2], Exception) else []
    weather = results[3] if not isinstance(results[3], Exception) else {}
    dest_coords = results[4] if not isinstance(results[4], Exception) else {"latitude": 0, "longitude": 0}
    flights = results[5] if len(results) > 5 and not isinstance(results[5], Exception) else []

    # Log any errors
    errors = state.get("errors", [])
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            error_msg = f"Search task {i} failed: {str(r)}"
            logger.error(error_msg)
            errors.append(error_msg)

    search_results = {
        "attractions": attractions if isinstance(attractions, list) else [],
        "restaurants": restaurants if isinstance(restaurants, list) else [],
        "hotels": hotels if isinstance(hotels, list) else [],
        "flights": flights if isinstance(flights, list) else [],
    }

    total_results = sum(len(v) for v in search_results.values())
    logger.info(f"[SEARCH] Search Agent: Found {total_results} total results")

    return {
        "search_results": search_results,
        "weather_data": weather if isinstance(weather, dict) else {},
        "destination_coords": dest_coords if isinstance(dest_coords, dict) else {"latitude": 0, "longitude": 0},
        "errors": errors,
        "agent_logs": state.get("agent_logs", []) + [
            f"Search: Found {len(search_results['attractions'])} attractions, "
            f"{len(search_results['restaurants'])} restaurants, "
            f"{len(search_results['hotels'])} hotels, "
            f"{len(search_results['flights'])} flights"
        ],
    }
