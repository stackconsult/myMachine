"""
Cache abstraction layer for CEP Machine
Supports DragonflyDB (Redis-compatible) caching
"""

import json
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Optional, Union
import os
import redis
from redis.asyncio import Redis as AsyncRedis
import logging

logger = logging.getLogger(__name__)

class CacheInterface(ABC):
    """Abstract interface for cache implementations"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache keys matching pattern"""
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value"""
        pass
    
    @abstractmethod
    async def get_info(self) -> dict:
        """Get cache statistics"""
        pass

class DragonflyCache(CacheInterface):
    """DragonflyDB cache implementation (Redis-compatible)"""
    
    def __init__(self):
        self.host = os.getenv('CACHE_HOST', 'localhost')
        self.port = int(os.getenv('CACHE_PORT', 6379))
        self.db = int(os.getenv('CACHE_DB', 0))
        self.password = os.getenv('CACHE_PASSWORD')
        self.max_connections = int(os.getenv('CACHE_MAX_CONNECTIONS', 20))
        
        self._client = None
        self._async_client = None
        
    async def connect(self):
        """Initialize Redis connection"""
        try:
            # Async client for main operations
            self._async_client = AsyncRedis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False,  # Handle bytes for pickle
                max_connections=self.max_connections,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self._async_client.ping()
            logger.info(f"Connected to DragonflyDB at {self.host}:{self.port}")
            
            # Sync client for some operations
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False
            )
            
        except Exception as e:
            logger.error(f"Failed to connect to DragonflyDB: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connections"""
        if self._async_client:
            await self._async_client.close()
        if self._client:
            self._client.close()
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage"""
        if isinstance(value, (str, int, float, bool)):
            return str(value).encode('utf-8')
        elif isinstance(value, (dict, list, tuple)):
            return json.dumps(value, default=str).encode('utf-8')
        else:
            return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage"""
        if not value:
            return None
        
        try:
            # Try JSON first
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Try pickle
                return pickle.loads(value)
            except pickle.PickleError:
                # Return as string
                return value.decode('utf-8', errors='ignore')
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._async_client:
            await self.connect()
        
        try:
            value = await self._async_client.get(key)
            if value:
                return self._deserialize(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
        if not self._async_client:
            await self.connect()
        
        try:
            serialized = self._serialize(value)
            if ttl:
                return await self._async_client.setex(key, ttl, serialized)
            else:
                return await self._async_client.set(key, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._async_client:
            await self.connect()
        
        try:
            return bool(await self._async_client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._async_client:
            await self.connect()
        
        try:
            return bool(await self._async_client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache keys matching pattern"""
        if not self._async_client:
            await self.connect()
        
        try:
            if pattern:
                keys = await self._async_client.keys(pattern)
                if keys:
                    return await self._async_client.delete(*keys)
                return 0
            else:
                return await self._async_client.flushdb()
        except Exception as e:
            logger.error(f"Cache clear error for pattern {pattern}: {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value"""
        if not self._async_client:
            await self.connect()
        
        try:
            return await self._async_client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    async def get_info(self) -> dict:
        """Get cache statistics"""
        if not self._client:
            await self.connect()
        
        try:
            info = self._client.info()
            return {
                'version': info.get('redis_version'),
                'used_memory': info.get('used_memory'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info)
            }
        except Exception as e:
            logger.error(f"Cache info error: {e}")
            return {}
    
    def _calculate_hit_rate(self, info: dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    async def pipeline(self):
        """Get pipeline for batch operations"""
        if not self._async_client:
            await self.connect()
        return self._async_client.pipeline()

# Cache instance
_cache_instance: Optional[DragonflyCache] = None

async def get_cache() -> DragonflyCache:
    """Get singleton cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DragonflyCache()
        await _cache_instance.connect()
    return _cache_instance

# Decorators for caching
def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cache = await get_cache()
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {cache_key}")
            
            return result
        return wrapper
    return decorator

# Cache key generators
def prospect_cache_key(location: str, category: str) -> str:
    """Generate cache key for prospect searches"""
    return f"prospects:{location}:{category}"

def pitch_cache_key(prospect_id: str, template: str) -> str:
    """Generate cache key for pitch generation"""
    return f"pitch:{prospect_id}:{template}"

def gbp_cache_key(business_id: str) -> str:
    """Generate cache key for GBP analysis"""
    return f"gbp:{business_id}"

def session_cache_key(session_id: str) -> str:
    """Generate cache key for sessions"""
    return f"session:{session_id}"

def rate_limit_cache_key(identifier: str, window: str) -> str:
    """Generate cache key for rate limiting"""
    return f"rate_limit:{identifier}:{window}"
