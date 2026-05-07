"""Redis cache helpers.

All functions are no-ops when Redis is unavailable so the app degrades
gracefully without any changes at the call site.
"""
import json
import logging
from typing import Any, Optional

from app.extensions import get_cache

logger = logging.getLogger(__name__)


def cache_get(key: str) -> Optional[Any]:
    """Return deserialized value or None (cache miss or Redis down)."""
    client = get_cache()
    if not client:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as exc:
        logger.warning("cache_get failed key=%s: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    """Serialize and store value with TTL (seconds). No-op on failure."""
    client = get_cache()
    if not client:
        return
    try:
        client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as exc:
        logger.warning("cache_set failed key=%s: %s", key, exc)


def cache_delete(*keys: str) -> None:
    """Delete one or more keys. No-op on failure."""
    client = get_cache()
    if not client or not keys:
        return
    try:
        client.delete(*keys)
    except Exception as exc:
        logger.warning("cache_delete failed keys=%s: %s", keys, exc)
