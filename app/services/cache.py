"""Cache service with TTL support and Redis-ready interface."""

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CacheInterface(ABC):
    """Abstract interface for cache implementations."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get the number of cached items."""
        pass

    @abstractmethod
    async def keys(self, limit: int = 10) -> List[str]:
        """Get a sample of cache keys."""
        pass


class CacheEntry:
    """A cache entry with value and expiry time."""

    def __init__(self, value: Any, ttl_seconds: Optional[int] = None):
        self.value = value
        self.created_at = datetime.utcnow()
        self.expires_at = (
            self.created_at + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        )

    @property
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class InMemoryCache(CacheInterface):
    """In-memory cache implementation with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
        self._access_order: List[str] = []  # For LRU eviction

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache, returns None if expired or not found."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired:
                # Remove expired entry
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                logger.debug(f"Cache entry expired: {key}")
                return None

            # Update access order for LRU
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            logger.debug(f"Cache hit: {key}")
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL."""
        async with self._lock:
            # Evict entries if at max capacity
            while len(self._cache) >= self._max_size and self._access_order:
                oldest_key = self._access_order.pop(0)
                if oldest_key in self._cache:
                    del self._cache[oldest_key]
                    logger.debug(f"Evicted cache entry: {oldest_key}")

            # Create new entry
            effective_ttl = ttl if ttl is not None else self._default_ttl
            self._cache[key] = CacheEntry(value, effective_ttl)

            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            logger.debug(f"Cache set: {key}")

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                logger.debug(f"Cache deleted: {key}")
                return True
            return False

    async def clear(self) -> None:
        """Clear all cached values."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            logger.info("Cache cleared")

    async def size(self) -> int:
        """Get the number of cached items (excluding expired)."""
        async with self._lock:
            # Clean up expired entries
            expired_keys = [k for k, v in self._cache.items() if v.is_expired]
            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
            return len(self._cache)

    async def keys(self, limit: int = 10) -> List[str]:
        """Get a sample of cache keys."""
        async with self._lock:
            return list(self._cache.keys())[:limit]


class CacheService:
    """High-level cache service with key generation utilities."""

    def __init__(self, cache: CacheInterface):
        self._cache = cache

    @staticmethod
    def generate_recipe_key(
        dish_name: str, servings: int, dietary_restrictions: Optional[List[str]] = None
    ) -> str:
        """Generate a unique cache key for a recipe request."""
        dietary_str = "_".join(sorted(dietary_restrictions)) if dietary_restrictions else ""
        key_string = f"{dish_name.lower().strip()}_{servings}_{dietary_str}"
        return hashlib.md5(key_string.encode()).hexdigest()

    async def get_recipe(
        self, dish_name: str, servings: int, dietary_restrictions: Optional[List[str]] = None
    ) -> Optional[Any]:
        """Get a cached recipe."""
        key = self.generate_recipe_key(dish_name, servings, dietary_restrictions)
        return await self._cache.get(key)

    async def set_recipe(
        self,
        dish_name: str,
        servings: int,
        recipe_data: Any,
        dietary_restrictions: Optional[List[str]] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache a recipe."""
        key = self.generate_recipe_key(dish_name, servings, dietary_restrictions)
        await self._cache.set(key, recipe_data, ttl)

    async def clear(self) -> None:
        """Clear all cached recipes."""
        await self._cache.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_recipes": await self._cache.size(),
            "cache_keys": await self._cache.keys(10),
        }


# Future Redis implementation stub
class RedisCache(CacheInterface):
    """Redis cache implementation for production use."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self._redis_url = redis_url
        self._client = None
        raise NotImplementedError(
            "Redis cache not yet implemented. Use InMemoryCache for now."
        )

    async def get(self, key: str) -> Optional[Any]:
        pass

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass

    async def delete(self, key: str) -> bool:
        pass

    async def clear(self) -> None:
        pass

    async def size(self) -> int:
        pass

    async def keys(self, limit: int = 10) -> List[str]:
        pass
