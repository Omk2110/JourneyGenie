"""
Map Agent -- converts places to coordinates and optimizes routes.
"""

from __future__ import annotations
import logging
from backend.agents.state import TravelPlannerState
from backend.tools.distance_matrix import get_route, haversine_distance

logger = logging.getLogger(__name__)


async def map_agent(state: TravelPlannerState) -> dict:
    """
    Process itinerary activities into map-ready data.
    Optimizes daily routes and generates coordinate groupings.
    """
    itinerary = state.get("itinerary", [])
    destination_coords = state.get("destination_coords", {})

    logger.info(f"[MAP] Map Agent: Processing {len(itinerary)} days of map data")

    map_data = []
    total_distance = 0.0
    total_travel_time = 0

    for day_plan in itinerary:
        day_num = day_plan.get("day", 1)
        activities = day_plan.get("activities", [])

        # Collect waypoints with valid coordinates
        waypoints = []
        activity_refs = []
        for idx, activity in enumerate(activities):
            lat = activity.get("latitude", 0.0)
            lng = activity.get("longitude", 0.0)
            if lat != 0.0 or lng != 0.0:
                waypoints.append((lat, lng))
                activity_refs.append(activity)

        # Optimize route for this day
        if len(waypoints) >= 2:
            route = await get_route(waypoints)
            optimized_order = route.get("optimized_order", list(range(len(waypoints))))
            total_distance += route.get("total_distance_km", 0)
            total_travel_time += route.get("total_duration_minutes", 0)

            # Update day's travel time in itinerary
            day_plan["travel_time_minutes"] = route.get("total_duration_minutes", 0)
        else:
            optimized_order = list(range(len(waypoints)))

        # Generate map points in optimized order
        for order_idx, wp_idx in enumerate(optimized_order):
            if wp_idx < len(activity_refs):
                activity = activity_refs[wp_idx]
                map_data.append({
                    "name": activity.get("name", "Unknown"),
                    "latitude": waypoints[wp_idx][0],
                    "longitude": waypoints[wp_idx][1],
                    "day": day_num,
                    "order": order_idx + 1,
                    "category": activity.get("category", "attraction"),
                })

    # Add destination center point
    if destination_coords.get("latitude"):
        map_data.insert(0, {
            "name": state.get("destination", "Destination"),
            "latitude": destination_coords.get("latitude", 0),
            "longitude": destination_coords.get("longitude", 0),
            "day": 0,  # 0 = destination marker
            "order": 0,
            "category": "destination",
        })

    logger.info(
        f"[MAP] Map Agent: {len(map_data)} points, "
        f"{total_distance:.1f}km total, {total_travel_time}min travel"
    )

    return {
        "map_data": map_data,
        "itinerary": itinerary,  # Updated with travel times
        "agent_logs": state.get("agent_logs", []) + [
            f"Map: Processed {len(map_data)} map points across {len(itinerary)} days "
            f"({total_distance:.1f}km total travel)"
        ],
    }
