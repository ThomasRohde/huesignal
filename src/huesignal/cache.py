"""Simple file-based cache with TTL support for CLI performance optimization."""

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Cache directory in user's home
CACHE_DIR = Path.home() / ".huesignal"
CACHE_FILE = CACHE_DIR / "cache.json"


class CacheManager:
    """Simple JSON-based cache with time-to-live (TTL) support."""

    def __init__(self, cache_file: Path = CACHE_FILE):
        """Initialize cache manager.

        Args:
            cache_file: Path to cache file (default: ~/.huesignal/cache.json)
        """
        self.cache_file = cache_file
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create cache directory: {e}")

    def _load_cache(self) -> dict[str, Any]:
        """Load cache from disk.

        Returns:
            Dictionary of cached data, or empty dict if cache doesn't exist or is invalid.
        """
        if not self.cache_file.exists():
            return {}

        try:
            with open(self.cache_file, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"Failed to load cache: {e}")
            return {}

    def _save_cache(self, data: dict[str, Any]) -> None:
        """Save cache to disk.

        Args:
            data: Dictionary to save as cache.
        """
        try:
            self._ensure_cache_dir()
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            logger.warning(f"Failed to save cache: {e}")

    def get(self, key: str, default: Any = None) -> Any | None:
        """Get value from cache if it exists and hasn't expired.

        Args:
            key: Cache key to retrieve.
            default: Default value if key doesn't exist or has expired.

        Returns:
            Cached value if valid, otherwise default.
        """
        cache = self._load_cache()

        if key not in cache:
            logger.debug(f"Cache miss: {key}")
            return default

        entry = cache[key]

        # Check if entry has expired
        if "expires_at" in entry:
            if time.time() > entry["expires_at"]:
                logger.debug(f"Cache expired: {key}")
                # Clean up expired entry
                del cache[key]
                self._save_cache(cache)
                return default

        logger.debug(f"Cache hit: {key}")
        return entry.get("value", default)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache with optional TTL.

        Args:
            key: Cache key to set.
            value: Value to cache (must be JSON-serializable).
            ttl: Time-to-live in seconds. If None, cache never expires.
        """
        cache = self._load_cache()

        entry = {"value": value}

        if ttl is not None:
            entry["expires_at"] = time.time() + ttl

        cache[key] = entry
        self._save_cache(cache)
        logger.debug(f"Cached: {key} (ttl={ttl}s)")

    def delete(self, key: str) -> bool:
        """Delete a specific key from cache.

        Args:
            key: Cache key to delete.

        Returns:
            True if key was deleted, False if it didn't exist.
        """
        cache = self._load_cache()

        if key in cache:
            del cache[key]
            self._save_cache(cache)
            logger.debug(f"Deleted from cache: {key}")
            return True

        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info("Cache cleared")
        except OSError as e:
            logger.warning(f"Failed to clear cache: {e}")

    def prune_expired(self) -> int:
        """Remove all expired entries from cache.

        Returns:
            Number of entries pruned.
        """
        cache = self._load_cache()
        now = time.time()
        pruned = 0

        keys_to_delete = [
            key for key, entry in cache.items()
            if "expires_at" in entry and now > entry["expires_at"]
        ]

        for key in keys_to_delete:
            del cache[key]
            pruned += 1

        if pruned > 0:
            self._save_cache(cache)
            logger.debug(f"Pruned {pruned} expired cache entries")

        return pruned


# Global cache instance
_cache = CacheManager()

# Cache keys
DEFAULT_BRIDGE_IP_KEY = "default_bridge_ip"
DEFAULT_BRIDGE_IP_TTL = 86400  # 24 hours


def get_cache() -> CacheManager:
    """Get the global cache instance.

    Returns:
        Global CacheManager instance.
    """
    return _cache


def get_default_bridge_ip() -> str | None:
    """Get the cached default bridge IP address.

    Returns:
        Cached bridge IP if available, None otherwise.
    """
    cache = get_cache()
    return cache.get(DEFAULT_BRIDGE_IP_KEY)


def set_default_bridge_ip(bridge_ip: str) -> None:
    """Cache the default bridge IP address.

    Args:
        bridge_ip: Bridge IP address to cache as default.
    """
    cache = get_cache()
    cache.set(DEFAULT_BRIDGE_IP_KEY, bridge_ip, ttl=DEFAULT_BRIDGE_IP_TTL)
    logger.debug(f"Cached default bridge IP: {bridge_ip}")
