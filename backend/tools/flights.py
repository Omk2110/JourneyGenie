"""
Flight search tool -- uses SerpApi Google Flights API for flight data.
Falls back to estimated pricing in INR when API key is missing.
"""

from __future__ import annotations
import logging
from datetime import datetime, timedelta
import httpx
from backend.config import settings
from backend.cache import cached
from backend.llm.provider import get_llm
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"


@cached(prefix="flight_dest")
async def _search_flight_destination(query: str) -> str | None:
    """Translate city/airport name to a 3-letter IATA code using LLM."""
    if not settings.SERPAPI_KEY:
        return None
    try:
        # We need a strict IATA code for SerpApi Google Flights
        llm = get_llm(temperature=0.0)
        prompt = f"Return strictly only the primary 3-letter IATA airport code for the main airport in this city/location: {query}. Do NOT return metropolitan codes (e.g. use JFK not NYC, LHR not LON). No other text, markdown, or punctuation."
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        
        content = response.content
        if isinstance(content, list):
            content = "".join([p.get("text", "") for p in content if isinstance(p, dict)])
            
        code = str(content).strip().replace("`", "").upper()[:3]
        if len(code) == 3 and code.isalpha():
            logger.debug(f"Translated '{query}' to IATA code: {code}")
            return code
            
        logger.warning(f"LLM returned invalid IATA format for '{query}': {response.content}")
        return None
    except Exception as e:
        logger.warning(f"Flight destination LLM translation error: {e}")
    return None


@cached(prefix="flights")
async def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
    max_results: int = 5,
) -> list[dict]:
    """
    Search for flights using SerpApi Google Flights.
    Returns price (INR), airline, duration, stops.
    Falls back to estimates when SERPAPI_KEY is not set.
    """
    if not settings.SERPAPI_KEY:
        logger.warning("SERPAPI_KEY not set -- using estimated flight prices (INR)")
        return _get_fallback_flights(origin, destination, adults, max_results)

    # Get origin and destination IATA IDs
    origin_id = await _search_flight_destination(origin) or origin[:3].upper()
    dest_id = await _search_flight_destination(destination) or destination[:3].upper()

    # Default departure date if not provided
    if not departure_date:
        departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "engine": "google_flights",
                "departure_id": origin_id,
                "arrival_id": dest_id,
                "outbound_date": departure_date,
                "type": "2", # 2 is One-way in Google Flights SerpApi
                "currency": "INR",
                "hl": "en",
                "api_key": settings.SERPAPI_KEY,
            }
            resp = await client.get(SERPAPI_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()

            results = []
            
            # Google flights SerpApi returns list in 'best_flights' and 'other_flights'
            flights = data.get("best_flights", []) or data.get("other_flights", []) or []

            for offer in flights[:max_results]:
                # Extract pricing
                total_price = float(offer.get("price", 0) or 0)

                # Extract segments from first flight offer
                flight_segments = offer.get("flights", [])
                
                airline = flight_segments[0].get("airline", "Unknown") if flight_segments else "Unknown"
                num_stops = max(0, len(flight_segments) - 1) if flight_segments else 0

                # Duration
                total_duration_minutes = offer.get("total_duration", 0)
                hours = total_duration_minutes // 60
                minutes = total_duration_minutes % 60
                duration_str = f"PT{hours}H{minutes}M" if total_duration_minutes else "N/A"

                # Departure time
                departure_time = flight_segments[0].get("departure_airport", {}).get("time", "") if flight_segments else ""

                results.append({
                    "airline": airline,
                    "price_per_person": round(total_price, 2), # prices in serpapi given per ticket
                    "total_price": round(total_price * adults, 2),
                    "duration": duration_str,
                    "stops": num_stops,
                    "departure": departure_time,
                    "source": "serpapi_google_flights",
                })

            if results:
                logger.info(f"SerpApi Flights: Found {len(results)} flights from '{origin_id}' to '{dest_id}'")
                return results

    except Exception as e:
        logger.error(f"SerpApi flight search error for {origin_id}->{dest_id}: {e}")

    return _get_fallback_flights(origin, destination, adults, max_results)


def _get_fallback_flights(origin: str, destination: str, adults: int, max_results: int) -> list[dict]:
    """Estimated flight prices in INR based on route distance heuristic."""

    # Determine if domestic (Indian) or international
    indian_cities = {"delhi", "mumbai", "bangalore", "chennai", "kolkata", "hyderabad",
                     "goa", "jaipur", "pune", "ahmedabad", "lucknow", "kerala",
                     "shimla", "manali", "varanasi", "agra", "udaipur", "srinagar",
                     "kochi", "thiruvananthapuram", "bhubaneswar", "patna", "indore"}

    origin_lower = origin.lower()
    dest_lower = destination.lower()
    is_domestic = any(c in origin_lower for c in indian_cities) and any(c in dest_lower for c in indian_cities)

    if is_domestic:
        base_prices = [
            {"airline": "IndiGo", "price": 4500, "duration": "PT2H15M", "stops": 0},
            {"airline": "SpiceJet", "price": 3800, "duration": "PT2H45M", "stops": 0},
            {"airline": "Air India", "price": 5500, "duration": "PT2H", "stops": 0},
            {"airline": "Vistara", "price": 6200, "duration": "PT2H10M", "stops": 0},
            {"airline": "Go First", "price": 4200, "duration": "PT3H30M", "stops": 1},
        ]
    else:
        base_prices = [
            {"airline": "Air India", "price": 28000, "duration": "PT8H", "stops": 0},
            {"airline": "Emirates", "price": 35000, "duration": "PT10H30M", "stops": 1},
            {"airline": "Lufthansa", "price": 42000, "duration": "PT9H", "stops": 1},
            {"airline": "Singapore Airlines", "price": 38000, "duration": "PT7H15M", "stops": 0},
            {"airline": "Qatar Airways", "price": 32000, "duration": "PT11H", "stops": 1},
        ]

    return [
        {
            "airline": f["airline"],
            "price_per_person": f["price"],
            "total_price": f["price"] * adults,
            "duration": f["duration"],
            "stops": f["stops"],
            "departure": "",
            "source": "fallback_estimate",
        }
        for f in base_prices[:max_results]
    ]
