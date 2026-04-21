"""
Distance matrix and route optimization tool.
Uses Geoapify Routing API with fallback to haversine estimates.
"""

from __future__ import annotations
import math
import logging
import httpx
from backend.config import settings
from backend.cache import cached

logger = logging.getLogger(__name__)

GEOAPIFY_ROUTING_URL = "https://api.geoapify.com/v1/routing"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def estimate_travel_time(distance_km: float) -> int:
    """Estimate travel time in minutes based on distance (urban driving speed ~30km/h)."""
    if distance_km < 2:
        return 10  # Walking distance
    elif distance_km < 10:
        return int(distance_km / 20 * 60)  # City traffic
    else:
        return int(distance_km / 40 * 60)  # Intercity


@cached(prefix="distance_matrix")
async def get_distance_matrix(
    origins: list[tuple[float, float]],
    destinations: list[tuple[float, float]],
) -> dict:
    """
    Get a distance matrix between origins and destinations.
    Uses Geoapify Routing API when available, falls back to haversine estimates.
    """
    if not settings.GEOAPIFY_API_KEY:
        return _get_fallback_matrix(origins, destinations)

    try:
        # Geoapify routing works best for point-to-point, so we build a matrix
        matrix = []
        for olat, olng in origins:
            row = []
            for dlat, dlng in destinations:
                # For short distances, haversine is fine and avoids API calls
                dist = haversine_distance(olat, olng, dlat, dlng)
                if dist < 50:  # Only use API for longer distances
                    row.append({
                        "distance_km": round(dist * 1.3, 2),  # Road distance factor
                        "duration_minutes": estimate_travel_time(dist),
                    })
                else:
                    # Use Geoapify for longer routes
                    route_data = await _geoapify_route(olat, olng, dlat, dlng)
                    if route_data:
                        row.append(route_data)
                    else:
                        row.append({
                            "distance_km": round(dist * 1.3, 2),
                            "duration_minutes": estimate_travel_time(dist),
                        })
            matrix.append(row)

        return {"matrix": matrix, "source": "geoapify"}

    except Exception as e:
        logger.error(f"Geoapify routing error: {e}")
        return _get_fallback_matrix(origins, destinations)


async def _geoapify_route(lat1: float, lon1: float, lat2: float, lon2: float) -> dict | None:
    """Get route data between two points using Geoapify."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "waypoints": f"{lat1},{lon1}|{lat2},{lon2}",
                "mode": "drive",
                "apiKey": settings.GEOAPIFY_API_KEY,
            }
            resp = await client.get(GEOAPIFY_ROUTING_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                distance_m = props.get("distance", 0)
                time_s = props.get("time", 0)
                return {
                    "distance_km": round(distance_m / 1000, 2),
                    "duration_minutes": round(time_s / 60, 1),
                }
    except Exception as e:
        logger.warning(f"Geoapify route error: {e}")
    return None


def _get_fallback_matrix(
    origins: list[tuple[float, float]],
    destinations: list[tuple[float, float]],
) -> dict:
    """Haversine-based distance matrix estimation."""
    matrix = []
    for olat, olng in origins:
        row = []
        for dlat, dlng in destinations:
            dist = haversine_distance(olat, olng, dlat, dlng)
            row.append({
                "distance_km": round(dist, 2),
                "duration_minutes": estimate_travel_time(dist),
            })
        matrix.append(row)
    return {"matrix": matrix, "source": "haversine_estimate"}


async def get_route(waypoints: list[tuple[float, float]]) -> dict:
    """
    Optimize route order using nearest-neighbor heuristic.
    Returns optimized order and total distance/time.
    """
    if len(waypoints) <= 1:
        return {
            "optimized_order": list(range(len(waypoints))),
            "total_distance_km": 0,
            "total_duration_minutes": 0,
            "legs": [],
        }

    # Nearest-neighbor TSP heuristic
    n = len(waypoints)
    visited = [False] * n
    order = [0]
    visited[0] = True
    total_dist = 0.0
    total_time = 0
    legs = []

    for _ in range(n - 1):
        current = order[-1]
        best_next = -1
        best_dist = float("inf")

        for j in range(n):
            if not visited[j]:
                dist = haversine_distance(
                    waypoints[current][0], waypoints[current][1],
                    waypoints[j][0], waypoints[j][1],
                )
                if dist < best_dist:
                    best_dist = dist
                    best_next = j

        if best_next >= 0:
            visited[best_next] = True
            order.append(best_next)
            travel_time = estimate_travel_time(best_dist)
            total_dist += best_dist
            total_time += travel_time
            legs.append({
                "from_index": current,
                "to_index": best_next,
                "distance_km": round(best_dist, 2),
                "duration_minutes": travel_time,
            })

    return {
        "optimized_order": order,
        "total_distance_km": round(total_dist, 2),
        "total_duration_minutes": total_time,
        "legs": legs,
    }
