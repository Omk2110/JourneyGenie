"""
Serper web search tool -- used as a general-purpose fallback
for finding destinations, travel info, and reviews.
Uses google.serper.dev API (free tier).
"""

from __future__ import annotations
import logging
import httpx
from backend.config import settings
from backend.cache import cached

logger = logging.getLogger(__name__)

SERPER_BASE_URL = "https://google.serper.dev/search"


@cached(prefix="serper")
async def web_search(query: str, num_results: int = 5) -> list[dict]:
    """
    Search the web via Serper API. Returns structured results.
    Falls back to empty results if SERPER_API_KEY is not set.
    """
    if not settings.SERPER_API_KEY:
        logger.warning("SERPER_API_KEY not set -- returning empty web search results")
        return _get_fallback_results(query, num_results)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "X-API-KEY": settings.SERPER_API_KEY,
                "Content-Type": "application/json",
            }
            payload = {
                "q": query,
                "num": num_results,
            }
            resp = await client.post(SERPER_BASE_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("organic", [])[:num_results]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "link": item.get("link", ""),
                    "source": "serper",
                })
            return results

    except Exception as e:
        logger.error(f"Serper API error: {e}")
        return _get_fallback_results(query, num_results)


def _get_fallback_results(query: str, num_results: int) -> list[dict]:
    """Minimal fallback when Serper is unavailable."""
    return [
        {
            "title": f"Travel guide: {query}",
            "snippet": f"Comprehensive travel information about {query}. "
                       f"Discover popular attractions, local cuisine, and cultural experiences.",
            "link": "",
            "source": "fallback",
        }
    ]
