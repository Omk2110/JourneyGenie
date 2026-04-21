"""
Places & attractions search tool -- uses OpenTripMap API.
Falls back to Serper web search, then to simulated data when APIs are unavailable.
"""

from __future__ import annotations
import logging
import httpx
from backend.config import settings
from backend.cache import cached

logger = logging.getLogger(__name__)

OTM_BASE_URL = "https://api.opentripmap.com/0.1/en/places"


async def _otm_geoname(city: str) -> dict | None:
    """Get lat/lon for a city via OpenTripMap geoname endpoint."""
    if not settings.OPENTRIPMAP_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "name": city,
                "apikey": settings.OPENTRIPMAP_API_KEY,
            }
            resp = await client.get(f"{OTM_BASE_URL}/geoname", params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("lat") and data.get("lon"):
                return {"lat": data["lat"], "lon": data["lon"], "name": data.get("name", city)}
    except Exception as e:
        logger.warning(f"OpenTripMap geoname error: {e}")
    return None


async def _otm_radius_search(
    lat: float, lon: float, kinds: str = "interesting_places", radius: int = 10000, limit: int = 20
) -> list[dict]:
    """Search places within a radius using OpenTripMap."""
    if not settings.OPENTRIPMAP_API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            params = {
                "radius": radius,
                "lon": lon,
                "lat": lat,
                "kinds": kinds,
                "rate": "3",  # Minimum rating 3 (only well-known places)
                "limit": limit,
                "apikey": settings.OPENTRIPMAP_API_KEY,
            }
            resp = await client.get(f"{OTM_BASE_URL}/radius", params=params)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("features", [])
    except Exception as e:
        logger.warning(f"OpenTripMap radius search error: {e}")
    return []


async def _otm_place_details(xid: str) -> dict | None:
    """Get detailed info for a specific place from OpenTripMap."""
    if not settings.OPENTRIPMAP_API_KEY or not xid:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {"apikey": settings.OPENTRIPMAP_API_KEY}
            resp = await client.get(f"{OTM_BASE_URL}/xid/{xid}", params=params)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"OpenTripMap place details error for {xid}: {e}")
    return None


def _category_to_otm_kinds(category: str) -> str:
    """Map our category names to OpenTripMap 'kinds' filter."""
    mapping = {
        "attraction": "interesting_places,cultural,historic,architecture",
        "restaurant": "foods,cafes,restaurants",
        "sightseeing": "interesting_places,view_points,natural",
        "museum": "museums,cultural",
        "nature": "natural,gardens_and_parks,beaches",
        "shopping": "shops,malls",
        "nightlife": "nightclubs,bars,pubs",
        "temple": "religion,historic",
        "adventure": "sport,amusements,extreme",
    }
    return mapping.get(category.lower(), "interesting_places,cultural,historic")


@cached(prefix="places")
async def search_places(
    query: str,
    location: str = "",
    category: str = "attraction",
    max_results: int = 10,
) -> list[dict]:
    """
    Search for places using OpenTripMap API.
    Fallback chain: OpenTripMap → Serper web search → hardcoded data.
    """
    # ── Try OpenTripMap first ────────────────────────────────
    if settings.OPENTRIPMAP_API_KEY:
        city = location or query
        geo = await _otm_geoname(city)

        if geo:
            kinds = _category_to_otm_kinds(category)
            raw_places = await _otm_radius_search(geo["lat"], geo["lon"], kinds=kinds, limit=max_results * 2)

            if raw_places:
                results = []
                for place in raw_places[:max_results * 2]:
                    # Handle both list-of-dicts and GeoJSON formats
                    if isinstance(place, dict):
                        props = place.get("properties", place)
                        geom = place.get("geometry", {}).get("coordinates", [])
                        name = props.get("name", "")
                        if not name:
                            continue

                        lat = props.get("point", {}).get("lat", geom[1] if len(geom) > 1 else 0)
                        lon = props.get("point", {}).get("lon", geom[0] if geom else 0)
                        xid = props.get("xid", "")

                        # Get details for enrichment (for top results only)
                        detail = None
                        if xid and len(results) < 8:
                            detail = await _otm_place_details(xid)

                        description = ""
                        if detail:
                            description = (
                                detail.get("wikipedia_extracts", {}).get("text", "")
                                or detail.get("info", {}).get("descr", "")
                                or f"Popular {category} in {city}"
                            )
                            # Truncate long descriptions
                            if len(description) > 200:
                                description = description[:197] + "..."

                        results.append({
                            "name": name,
                            "category": category,
                            "price": _estimate_price_inr(category),
                            "rating": min(props.get("rate", 3) + 1, 5.0),
                            "latitude": lat,
                            "longitude": lon,
                            "address": detail.get("address", {}).get("road", city) if detail else city,
                            "description": description or f"Popular {category} in {city}",
                            "image_url": detail.get("preview", {}).get("source", "") if detail else "",
                            "source": "opentripmap",
                        })

                        if len(results) >= max_results:
                            break

                if results:
                    logger.info(f"OpenTripMap: Found {len(results)} places for '{query}' in '{city}'")
                    return results

    # ── Fallback: Serper web search ──────────────────────────
    if settings.SERPER_API_KEY:
        logger.info(f"Falling back to Serper for places: {query}")
        try:
            from backend.tools.serpapi_search import web_search
            search_results = await web_search(f"top {category}s in {location or query} travel", 5)
            if search_results and search_results[0].get("source") != "fallback":
                return [
                    {
                        "name": r.get("title", "").split(" - ")[0].split(" | ")[0][:50],
                        "category": category,
                        "price": _estimate_price_inr(category),
                        "rating": 4.0,
                        "latitude": 0.0,
                        "longitude": 0.0,
                        "address": location or query,
                        "description": r.get("snippet", "")[:200],
                        "image_url": "",
                        "source": "serper_fallback",
                    }
                    for r in search_results[:max_results]
                ]
        except Exception as e:
            logger.warning(f"Serper fallback for places failed: {e}")

    # ── Final fallback: hardcoded data ───────────────────────
    logger.warning("All place APIs unavailable -- using simulated places data")
    return _get_fallback_places(query, category, max_results)


def _estimate_price_inr(category: str) -> float:
    """Estimate entry price in INR based on category."""
    prices = {
        "attraction": 500,
        "museum": 300,
        "restaurant": 800,
        "sightseeing": 0,
        "nature": 100,
        "temple": 0,
        "adventure": 1500,
        "shopping": 0,
        "nightlife": 1000,
    }
    return prices.get(category.lower(), 250)


def _get_fallback_places(query: str, category: str, max_results: int) -> list[dict]:
    """Generate simulated place data when all APIs are unavailable."""
    fallback_db = {
        "paris": [
            {"name": "Eiffel Tower", "lat": 48.8584, "lng": 2.2945, "rating": 4.7, "price": 2100},
            {"name": "Louvre Museum", "lat": 48.8606, "lng": 2.3376, "rating": 4.8, "price": 1800},
            {"name": "Notre-Dame Cathedral", "lat": 48.8530, "lng": 2.3499, "rating": 4.7, "price": 0},
            {"name": "Sacré-Cœur Basilica", "lat": 48.8867, "lng": 2.3431, "rating": 4.6, "price": 0},
            {"name": "Arc de Triomphe", "lat": 48.8738, "lng": 2.2950, "rating": 4.6, "price": 1300},
            {"name": "Musée d'Orsay", "lat": 48.8600, "lng": 2.3266, "rating": 4.7, "price": 1500},
            {"name": "Palace of Versailles", "lat": 48.8049, "lng": 2.1204, "rating": 4.6, "price": 1750},
            {"name": "Montmartre Quarter", "lat": 48.8862, "lng": 2.3411, "rating": 4.5, "price": 0},
        ],
        "tokyo": [
            {"name": "Senso-ji Temple", "lat": 35.7148, "lng": 139.7967, "rating": 4.6, "price": 0},
            {"name": "Meiji Shrine", "lat": 35.6764, "lng": 139.6993, "rating": 4.5, "price": 0},
            {"name": "Tokyo Tower", "lat": 35.6586, "lng": 139.7454, "rating": 4.4, "price": 1000},
            {"name": "Shibuya Crossing", "lat": 35.6595, "lng": 139.7004, "rating": 4.3, "price": 0},
            {"name": "Tsukiji Outer Market", "lat": 35.6654, "lng": 139.7707, "rating": 4.4, "price": 1600},
            {"name": "Imperial Palace", "lat": 35.6852, "lng": 139.7528, "rating": 4.3, "price": 0},
            {"name": "Akihabara District", "lat": 35.7023, "lng": 139.7745, "rating": 4.2, "price": 800},
            {"name": "TeamLab Borderless", "lat": 35.6264, "lng": 139.7836, "rating": 4.5, "price": 2700},
        ],
        "goa": [
            {"name": "Basilica of Bom Jesus", "lat": 15.5009, "lng": 73.9116, "rating": 4.6, "price": 0},
            {"name": "Fort Aguada", "lat": 15.4929, "lng": 73.7735, "rating": 4.4, "price": 50},
            {"name": "Baga Beach", "lat": 15.5551, "lng": 73.7514, "rating": 4.5, "price": 0},
            {"name": "Dudhsagar Falls", "lat": 15.3144, "lng": 74.3143, "rating": 4.7, "price": 400},
            {"name": "Anjuna Flea Market", "lat": 15.5754, "lng": 73.7442, "rating": 4.3, "price": 0},
            {"name": "Se Cathedral", "lat": 15.5038, "lng": 73.9127, "rating": 4.4, "price": 0},
            {"name": "Calangute Beach", "lat": 15.5439, "lng": 73.7554, "rating": 4.3, "price": 0},
            {"name": "Chapora Fort", "lat": 15.6047, "lng": 73.7360, "rating": 4.5, "price": 0},
        ],
        "delhi": [
            {"name": "Red Fort", "lat": 28.6562, "lng": 77.2410, "rating": 4.5, "price": 50},
            {"name": "Qutub Minar", "lat": 28.5245, "lng": 77.1855, "rating": 4.6, "price": 40},
            {"name": "India Gate", "lat": 28.6129, "lng": 77.2295, "rating": 4.6, "price": 0},
            {"name": "Humayun's Tomb", "lat": 28.5933, "lng": 77.2507, "rating": 4.7, "price": 50},
            {"name": "Lotus Temple", "lat": 28.5535, "lng": 77.2588, "rating": 4.5, "price": 0},
            {"name": "Jama Masjid", "lat": 28.6507, "lng": 77.2334, "rating": 4.4, "price": 0},
            {"name": "Chandni Chowk", "lat": 28.6506, "lng": 77.2300, "rating": 4.3, "price": 0},
            {"name": "Akshardham Temple", "lat": 28.6127, "lng": 77.2773, "rating": 4.7, "price": 0},
        ],
        "mumbai": [
            {"name": "Gateway of India", "lat": 18.9220, "lng": 72.8347, "rating": 4.6, "price": 0},
            {"name": "Marine Drive", "lat": 18.9432, "lng": 72.8235, "rating": 4.7, "price": 0},
            {"name": "Elephanta Caves", "lat": 18.9633, "lng": 72.9315, "rating": 4.4, "price": 40},
            {"name": "Haji Ali Dargah", "lat": 18.9827, "lng": 72.8089, "rating": 4.5, "price": 0},
            {"name": "Siddhivinayak Temple", "lat": 19.0169, "lng": 72.8302, "rating": 4.6, "price": 0},
            {"name": "Colaba Causeway", "lat": 18.9173, "lng": 72.8307, "rating": 4.3, "price": 0},
            {"name": "Juhu Beach", "lat": 19.0883, "lng": 72.8264, "rating": 4.2, "price": 0},
            {"name": "Chhatrapati Shivaji Terminus", "lat": 18.9398, "lng": 72.8355, "rating": 4.5, "price": 0},
        ],
        "jaipur": [
            {"name": "Hawa Mahal", "lat": 26.9239, "lng": 75.8267, "rating": 4.5, "price": 50},
            {"name": "Amber Fort", "lat": 26.9855, "lng": 75.8513, "rating": 4.7, "price": 200},
            {"name": "City Palace", "lat": 26.9258, "lng": 75.8237, "rating": 4.5, "price": 500},
            {"name": "Jantar Mantar", "lat": 26.9248, "lng": 75.8246, "rating": 4.3, "price": 50},
            {"name": "Nahargarh Fort", "lat": 26.9372, "lng": 75.8155, "rating": 4.5, "price": 50},
            {"name": "Jal Mahal", "lat": 26.9530, "lng": 75.8461, "rating": 4.4, "price": 0},
            {"name": "Albert Hall Museum", "lat": 26.9117, "lng": 75.8194, "rating": 4.3, "price": 40},
            {"name": "Birla Mandir", "lat": 26.8920, "lng": 75.8129, "rating": 4.5, "price": 0},
        ],
    }

    # Try exact match then partial match
    query_lower = query.lower()
    places = []
    for key, data in fallback_db.items():
        if key in query_lower or query_lower in key:
            places = data
            break

    # Generic fallback
    if not places:
        places = [
            {"name": f"{query} Main Square", "lat": 0.0, "lng": 0.0, "rating": 4.3, "price": 0},
            {"name": f"{query} National Museum", "lat": 0.0, "lng": 0.0, "rating": 4.5, "price": 250},
            {"name": f"{query} Historic Temple", "lat": 0.0, "lng": 0.0, "rating": 4.4, "price": 100},
            {"name": f"{query} Botanical Garden", "lat": 0.0, "lng": 0.0, "rating": 4.2, "price": 150},
            {"name": f"{query} Food Market", "lat": 0.0, "lng": 0.0, "rating": 4.6, "price": 500},
            {"name": f"{query} Observation Deck", "lat": 0.0, "lng": 0.0, "rating": 4.3, "price": 600},
            {"name": f"{query} Art Gallery", "lat": 0.0, "lng": 0.0, "rating": 4.4, "price": 200},
            {"name": f"{query} City Park", "lat": 0.0, "lng": 0.0, "rating": 4.5, "price": 0},
        ]

    return [
        {
            "name": p["name"],
            "category": category,
            "price": p["price"],
            "rating": p["rating"],
            "latitude": p["lat"],
            "longitude": p["lng"],
            "address": f"{query}",
            "description": f"Popular {category} in {query}",
            "image_url": "",
            "source": "fallback",
        }
        for p in places[:max_results]
    ]
