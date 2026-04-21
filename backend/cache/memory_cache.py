"""
In-memory TTL cache for API responses.
Uses a dictionary with timestamp-based expiry.
"""

from __future__ import annotations
import time
import hashlib
import json
import logging
from typing import Any, Callable
from functools import wraps
from backend.config import settings

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, Any]] = {}


def _make_key(prefix: str, *args, **kwargs) -> str:
    """Create a deterministic cache key from function arguments."""
    raw = json.dumps({"prefix": prefix, "args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()


def cached(prefix: str, ttl: int | None = None):
    """Decorator that caches async function results with TTL expiry."""
    ttl = ttl or settings.CACHE_TTL_SECONDS

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = _make_key(prefix, *args, **kwargs)
            now = time.time()

            # Check cache
            if key in _cache:
                timestamp, value = _cache[key]
                if now - timestamp < ttl:
                    logger.debug(f"Cache HIT: {prefix} [{key[:8]}]")
                    return value
                else:
                    del _cache[key]

            # Execute and cache
            logger.debug(f"Cache MISS: {prefix} [{key[:8]}]")
            result = await func(*args, **kwargs)
            _cache[key] = (now, result)
            return result

        return wrapper
    return decorator


def clear_cache():
    """Clear all cached entries."""
    _cache.clear()
    logger.info("Cache cleared")


def get_cache_stats() -> dict:
    """Get cache statistics."""
    now = time.time()
    ttl = settings.CACHE_TTL_SECONDS
    valid = sum(1 for ts, _ in _cache.values() if now - ts < ttl)
    return {
        "total_entries": len(_cache),
        "valid_entries": valid,
        "expired_entries": len(_cache) - valid,
    }
