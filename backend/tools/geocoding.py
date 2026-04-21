"""
Geocoding tool -- converts place names to coordinates and vice versa.
Uses Geoapify Geocoding API with fallback to known coordinates.
"""

from __future__ import annotations
import logging
import httpx
from backend.config import settings
from backend.cache import cached

logger = logging.getLogger(__name__)

GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
GEOAPIFY_REVERSE_URL = "https://api.geoapify.com/v1/geocode/reverse"


@cached(prefix="geocode")
async def geocode_place(place_name: str) -> dict:
    """
    Convert a place name to latitude/longitude coordinates using Geoapify.
    Falls back to known city coordinates when API key is missing.
    """
    if not settings.GEOAPIFY_API_KEY:
        logger.warning("GEOAPIFY_API_KEY not set -- using known coordinates")
        return _get_fallback_coordinates(place_name)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "text": place_name,
                "apiKey": settings.GEOAPIFY_API_KEY,
                "limit": 1,
                "format": "json",
            }
            resp = await client.get(GEOAPIFY_GEOCODE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if results:
                result = results[0]
                return {
                    "latitude": result.get("lat", 0.0),
                    "longitude": result.get("lon", 0.0),
                    "formatted_address": result.get("formatted", place_name),
                    "source": "geoapify",
                }

    except Exception as e:
        logger.error(f"Geoapify geocoding error: {e}")

    return _get_fallback_coordinates(place_name)


@cached(prefix="reverse_geocode")
async def reverse_geocode(latitude: float, longitude: float) -> dict:
    """Convert coordinates to a place name using Geoapify."""
    if not settings.GEOAPIFY_API_KEY:
        return {"address": f"Location ({latitude:.4f}, {longitude:.4f})", "source": "fallback"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "lat": latitude,
                "lon": longitude,
                "apiKey": settings.GEOAPIFY_API_KEY,
                "format": "json",
            }
            resp = await client.get(GEOAPIFY_REVERSE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if results:
                return {
                    "address": results[0].get("formatted", ""),
                    "source": "geoapify",
                }
    except Exception as e:
        logger.error(f"Geoapify reverse geocoding error: {e}")

    return {"address": f"Location ({latitude:.4f}, {longitude:.4f})", "source": "fallback"}


def _get_fallback_coordinates(place_name: str) -> dict:
    """Known coordinates for popular destinations."""
    known_cities = {
        "paris": {"lat": 48.8566, "lng": 2.3522},
        "tokyo": {"lat": 35.6762, "lng": 139.6503},
        "new york": {"lat": 40.7128, "lng": -74.0060},
        "london": {"lat": 51.5074, "lng": -0.1278},
        "dubai": {"lat": 25.2048, "lng": 55.2708},
        "bali": {"lat": -8.3405, "lng": 115.0920},
        "rome": {"lat": 41.9028, "lng": 12.4964},
        "bangkok": {"lat": 13.7563, "lng": 100.5018},
        "sydney": {"lat": -33.8688, "lng": 151.2093},
        "barcelona": {"lat": 41.3874, "lng": 2.1686},
        "istanbul": {"lat": 41.0082, "lng": 28.9784},
        "amsterdam": {"lat": 52.3676, "lng": 4.9041},
        "singapore": {"lat": 1.3521, "lng": 103.8198},
        # Indian cities
        "mumbai": {"lat": 19.0760, "lng": 72.8777},
        "delhi": {"lat": 28.7041, "lng": 77.1025},
        "new delhi": {"lat": 28.6139, "lng": 77.2090},
        "bangalore": {"lat": 12.9716, "lng": 77.5946},
        "bengaluru": {"lat": 12.9716, "lng": 77.5946},
        "chennai": {"lat": 13.0827, "lng": 80.2707},
        "kolkata": {"lat": 22.5726, "lng": 88.3639},
        "hyderabad": {"lat": 17.3850, "lng": 78.4867},
        "goa": {"lat": 15.2993, "lng": 74.1240},
        "jaipur": {"lat": 26.9124, "lng": 75.7873},
        "pune": {"lat": 18.5204, "lng": 73.8567},
        "ahmedabad": {"lat": 23.0225, "lng": 72.5714},
        "lucknow": {"lat": 26.8467, "lng": 80.9462},
        "kerala": {"lat": 10.8505, "lng": 76.2711},
        "kochi": {"lat": 9.9312, "lng": 76.2673},
        "shimla": {"lat": 31.1048, "lng": 77.1734},
        "manali": {"lat": 32.2396, "lng": 77.1887},
        "varanasi": {"lat": 25.3176, "lng": 82.9739},
        "agra": {"lat": 27.1767, "lng": 78.0081},
        "udaipur": {"lat": 24.5854, "lng": 73.7125},
        "rishikesh": {"lat": 30.0869, "lng": 78.2676},
        "darjeeling": {"lat": 27.0360, "lng": 88.2627},
        "srinagar": {"lat": 34.0837, "lng": 74.7973},
        "amritsar": {"lat": 31.6340, "lng": 74.8723},
        "mysore": {"lat": 12.2958, "lng": 76.6394},
        "mysuru": {"lat": 12.2958, "lng": 76.6394},
        "coorg": {"lat": 12.3375, "lng": 75.8069},
        "ooty": {"lat": 11.4102, "lng": 76.6950},
        "munnar": {"lat": 10.0889, "lng": 77.0595},
        "pondicherry": {"lat": 11.9416, "lng": 79.8083},
        "berlin": {"lat": 52.5200, "lng": 13.4050},
        "los angeles": {"lat": 34.0522, "lng": -118.2437},
        "san francisco": {"lat": 37.7749, "lng": -122.4194},
        "cairo": {"lat": 30.0444, "lng": 31.2357},
        "cape town": {"lat": -33.9249, "lng": 18.4241},
        "rio de janeiro": {"lat": -22.9068, "lng": -43.1729},
        "seoul": {"lat": 37.5665, "lng": 126.9780},
        "beijing": {"lat": 39.9042, "lng": 116.4074},
        "vienna": {"lat": 48.2082, "lng": 16.3738},
        "prague": {"lat": 50.0755, "lng": 14.4378},
        "lisbon": {"lat": 38.7223, "lng": -9.1393},
        "athens": {"lat": 37.9838, "lng": 23.7275},
        "zurich": {"lat": 47.3769, "lng": 8.5417},
    }

    place_lower = place_name.lower()
    for key, coords in known_cities.items():
        if key in place_lower or place_lower in key:
            return {
                "latitude": coords["lat"],
                "longitude": coords["lng"],
                "formatted_address": place_name,
                "source": "fallback_known",
            }

    return {
        "latitude": 0.0,
        "longitude": 0.0,
        "formatted_address": place_name,
        "source": "fallback_unknown",
    }
