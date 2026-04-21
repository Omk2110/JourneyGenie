"""
Weather tool -- retrieves current/forecast weather data.
Uses WeatherAPI.com (free tier).
Falls back to seasonal estimates when API key is missing.
"""

from __future__ import annotations
import logging
import httpx
from backend.config import settings
from backend.cache import cached

logger = logging.getLogger(__name__)

WEATHERAPI_BASE_URL = "https://api.weatherapi.com/v1"


@cached(prefix="weather")
async def get_weather(city: str, country_code: str = "") -> dict:
    """
    Get weather data for a city using WeatherAPI.com.
    Returns temperature, description, humidity.
    Falls back to seasonal averages when WEATHERAPI_API_KEY is not set.
    """
    if not settings.WEATHERAPI_API_KEY:
        logger.warning("WEATHERAPI_API_KEY not set -- using seasonal estimates")
        return _get_fallback_weather(city)

    try:
        query = f"{city},{country_code}" if country_code else city
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "key": settings.WEATHERAPI_API_KEY,
                "q": query,
                "aqi": "yes",
            }
            resp = await client.get(f"{WEATHERAPI_BASE_URL}/current.json", params=params)
            resp.raise_for_status()
            data = resp.json()

            current = data.get("current", {})
            condition = current.get("condition", {})

            return {
                "city": city,
                "temperature_celsius": current.get("temp_c", 20),
                "feels_like": current.get("feelslike_c", 20),
                "humidity": current.get("humidity", 60),
                "description": condition.get("text", "clear sky").lower(),
                "icon": condition.get("icon", ""),
                "wind_speed_mps": current.get("wind_kph", 10) / 3.6,  # Convert km/h to m/s
                "uv_index": current.get("uv", 0),
                "visibility_km": current.get("vis_km", 10),
                "source": "weatherapi",
            }

    except Exception as e:
        logger.error(f"WeatherAPI error: {e}")
        return _get_fallback_weather(city)


@cached(prefix="weather_forecast")
async def get_weather_forecast(city: str, days: int = 3) -> list[dict]:
    """
    Get weather forecast for multiple days using WeatherAPI.com.
    """
    if not settings.WEATHERAPI_API_KEY:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {
                "key": settings.WEATHERAPI_API_KEY,
                "q": city,
                "days": min(days, 10),  # WeatherAPI free tier supports up to 3 days
                "aqi": "yes",
            }
            resp = await client.get(f"{WEATHERAPI_BASE_URL}/forecast.json", params=params)
            resp.raise_for_status()
            data = resp.json()

            forecast_days = []
            for day_data in data.get("forecast", {}).get("forecastday", []):
                day_info = day_data.get("day", {})
                forecast_days.append({
                    "date": day_data.get("date", ""),
                    "max_temp_c": day_info.get("maxtemp_c", 25),
                    "min_temp_c": day_info.get("mintemp_c", 15),
                    "avg_temp_c": day_info.get("avgtemp_c", 20),
                    "description": day_info.get("condition", {}).get("text", ""),
                    "chance_of_rain": day_info.get("daily_chance_of_rain", 0),
                    "humidity": day_info.get("avghumidity", 60),
                    "uv_index": day_info.get("uv", 0),
                })
            return forecast_days

    except Exception as e:
        logger.error(f"WeatherAPI forecast error: {e}")
        return []


def _get_fallback_weather(city: str) -> dict:
    """Seasonal weather estimates for common destinations."""
    estimates = {
        "paris": {"temp": 14, "desc": "partly cloudy", "humidity": 65},
        "tokyo": {"temp": 17, "desc": "clear sky", "humidity": 55},
        "new york": {"temp": 15, "desc": "partly cloudy", "humidity": 60},
        "london": {"temp": 12, "desc": "light rain", "humidity": 70},
        "dubai": {"temp": 33, "desc": "clear sky", "humidity": 45},
        "bali": {"temp": 28, "desc": "scattered clouds", "humidity": 80},
        "rome": {"temp": 18, "desc": "clear sky", "humidity": 55},
        "bangkok": {"temp": 35, "desc": "thunderstorm", "humidity": 75},
        "sydney": {"temp": 22, "desc": "clear sky", "humidity": 60},
        "barcelona": {"temp": 17, "desc": "clear sky", "humidity": 65},
        # Indian cities
        "goa": {"temp": 32, "desc": "sunny", "humidity": 70},
        "delhi": {"temp": 35, "desc": "clear sky", "humidity": 40},
        "mumbai": {"temp": 30, "desc": "partly cloudy", "humidity": 75},
        "jaipur": {"temp": 36, "desc": "clear sky", "humidity": 30},
        "bangalore": {"temp": 27, "desc": "partly cloudy", "humidity": 55},
        "kolkata": {"temp": 33, "desc": "scattered clouds", "humidity": 70},
        "chennai": {"temp": 34, "desc": "sunny", "humidity": 65},
        "hyderabad": {"temp": 35, "desc": "clear sky", "humidity": 40},
        "kerala": {"temp": 29, "desc": "light rain", "humidity": 80},
        "shimla": {"temp": 20, "desc": "partly cloudy", "humidity": 50},
        "manali": {"temp": 15, "desc": "clear sky", "humidity": 45},
        "varanasi": {"temp": 34, "desc": "clear sky", "humidity": 50},
        "agra": {"temp": 36, "desc": "clear sky", "humidity": 35},
        "udaipur": {"temp": 35, "desc": "clear sky", "humidity": 30},
    }

    city_lower = city.lower()
    est = None
    for key, val in estimates.items():
        if key in city_lower or city_lower in key:
            est = val
            break

    if not est:
        est = {"temp": 22, "desc": "partly cloudy", "humidity": 60}

    return {
        "city": city,
        "temperature_celsius": est["temp"],
        "feels_like": est["temp"] - 2,
        "humidity": est["humidity"],
        "description": est["desc"],
        "icon": "",
        "wind_speed_mps": 4,
        "source": "fallback_estimate",
    }
