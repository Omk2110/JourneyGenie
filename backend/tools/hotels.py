"""
Hotel search tool -- uses SerpApi Google Hotels API.
Falls back to estimated pricing in INR when API key is missing.
"""

from __future__ import annotations
import logging
from datetime import datetime, timedelta
import httpx
from backend.config import settings
from backend.cache import cached

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"


@cached(prefix="hotels")
async def search_hotels(
    destination: str,
    checkin_date: str = "",
    checkout_date: str = "",
    adults: int = 2,
    rooms: int = 1,
    max_results: int = 8,
) -> list[dict]:
    """
    Search for hotels using SerpApi Google Hotels.
    Returns name, price (INR), rating, location.
    Falls back to estimates when SERPAPI_KEY is not set.
    """
    if not settings.SERPAPI_KEY:
        logger.warning("SERPAPI_KEY not set -- using estimated hotel prices (INR)")
        return _get_fallback_hotels(destination, adults, max_results)

    # Default dates if not provided
    if not checkin_date:
        checkin_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    if not checkout_date:
        checkout_date = (datetime.now() + timedelta(days=33)).strftime("%Y-%m-%d")

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            params = {
                "engine": "google_hotels",
                "q": destination,
                "check_in_date": checkin_date,
                "check_out_date": checkout_date,
                "adults": adults,
                "currency": "INR",
                "api_key": settings.SERPAPI_KEY,
            }
            resp = await client.get(SERPAPI_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()

            results = []
            hotels = data.get("properties", [])

            for hotel in hotels[:max_results]:
                # Extract pricing
                rate_info = hotel.get("rate_per_night", {})
                price = float(rate_info.get("extracted_lowest", 0) or 0)
                
                # Extract rating and class
                review_score = float(hotel.get("overall_rating", 0) or 0)
                
                class_str = hotel.get("hotel_class", "")
                stars = 3
                if class_str and class_str[0].isdigit():
                    stars = int(class_str[0])

                gps = hotel.get("gps_coordinates", {})
                
                results.append({
                    "name": hotel.get("name", "Unknown Hotel"),
                    "category": "hotel",
                    "price_per_night": round(price, 2),
                    "rating": review_score,
                    "stars": stars,
                    "latitude": float(gps.get("latitude", 0)),
                    "longitude": float(gps.get("longitude", 0)),
                    "address": destination, # SerpAPI Google Hotels uses generic locations unless we reverse geocode
                    "description": hotel.get("description", "Google Hotel Accommodation"),
                    "source": "serpapi_google_hotels",
                })

            if results:
                logger.info(f"SerpApi Hotels: Found {len(results)} hotels for '{destination}'")
                return results

    except Exception as e:
        logger.error(f"SerpApi hotel search error: {e}")

    return _get_fallback_hotels(destination, adults, max_results)


def _get_fallback_hotels(destination: str, adults: int, max_results: int) -> list[dict]:
    """Estimated hotel data in INR based on destination."""
    dest_lower = destination.lower()

    # Price multipliers by city tier (base prices in INR)
    multiplier = 1.0
    expensive_cities = ["tokyo", "london", "new york", "paris", "dubai", "zurich", "singapore"]
    mid_cities = ["rome", "barcelona", "berlin", "amsterdam", "sydney", "bangkok"]
    indian_cities = ["goa", "delhi", "mumbai", "jaipur", "bangalore", "chennai", "kolkata", "hyderabad",
                     "kerala", "shimla", "manali", "varanasi", "agra", "udaipur"]

    for city in expensive_cities:
        if city in dest_lower:
            multiplier = 3.0  # International expensive
            break
    for city in mid_cities:
        if city in dest_lower:
            multiplier = 2.0  # International mid
            break
    for city in indian_cities:
        if city in dest_lower:
            multiplier = 1.0  # Indian base rates
            break

    base_hotels = [
        {"name": f"Budget Inn {destination}", "price": 1200, "rating": 3.5, "stars": 2, "type": "budget"},
        {"name": f"{destination} Hostel Central", "price": 800, "rating": 3.8, "stars": 1, "type": "hostel"},
        {"name": f"Comfort Hotel {destination}", "price": 2500, "rating": 4.0, "stars": 3, "type": "mid-range"},
        {"name": f"{destination} City Suites", "price": 4000, "rating": 4.2, "stars": 4, "type": "mid-range"},
        {"name": f"Grand {destination} Hotel", "price": 6500, "rating": 4.5, "stars": 4, "type": "premium"},
        {"name": f"The {destination} Palace", "price": 12000, "rating": 4.7, "stars": 5, "type": "luxury"},
        {"name": f"{destination} Boutique Stay", "price": 3500, "rating": 4.3, "stars": 3, "type": "boutique"},
        {"name": f"Residence {destination}", "price": 2000, "rating": 4.1, "stars": 3, "type": "apartment"},
    ]

    return [
        {
            "name": h["name"],
            "category": "hotel",
            "price_per_night": round(h["price"] * multiplier, 2),
            "rating": h["rating"],
            "stars": h["stars"],
            "latitude": 0.0,
            "longitude": 0.0,
            "address": f"Central {destination}",
            "description": f"{h['type'].title()} accommodation in {destination}",
            "source": "fallback_estimate",
        }
        for h in base_hotels[:max_results]
    ]
