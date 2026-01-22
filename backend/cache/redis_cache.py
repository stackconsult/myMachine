"""
Redis Caching Implementation for CEP Machine
Production-ready caching with connection pooling and error handling
"""

import redis.asyncio as redis
import json
from typing import Any, Optional, List, Dict
import pickle
from datetime import timedelta
import os
import logging
import hashlib

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache implementation with connection pooling"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = None
        self._connected = False
    
    async def connect(self):
        """Initialize Redis connection"""
        if not self._connected:
            try:
                self._redis = redis.from_url(
                    self.redis_url,
                    decode_responses=False,
                    max_connections=20,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True
                )
                await self._redis.ping()
                self._connected = True
                logger.info("Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed: {str(e)}. Using fallback.")
                self._connected = False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Redis connection closed")
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return None
        
        try:
            data = await self._redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return False
        
        try:
            data = pickle.dumps(value)
            await self._redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return False
        
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return False
        
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {str(e)}")
            return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return {}
        
        try:
            values = await self._redis.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    result[key] = pickle.loads(value)
            return result
        except Exception as e:
            logger.error(f"Redis MGET error: {str(e)}")
            return {}
    
    async def set_many(self, mapping: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set multiple values in cache"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return False
        
        try:
            pipe = self._redis.pipeline()
            for key, value in mapping.items():
                data = pickle.dumps(value)
                pipe.setex(key, ttl, data)
            await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis MSET error: {str(e)}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return 0
        
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self._redis.delete(*keys)
            return len(keys)
        except Exception as e:
            logger.error(f"Redis DELETE PATTERN error: {str(e)}")
            return 0
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return None
        
        try:
            return await self._redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {str(e)}")
            return None
    
    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return None
        
        try:
            return await self._redis.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key {key}: {str(e)}")
            return None
    
    # Domain-specific caching methods
    
    def _generate_cache_key(self, prefix: str, *args) -> str:
        """Generate a consistent cache key"""
        key_parts = [str(arg).lower().replace(" ", "_") for arg in args]
        key_string = ":".join(key_parts)
        return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()[:16]}"
    
    async def get_cached_prospects(self, location: str, category: str) -> Optional[List[Dict]]:
        """Get cached prospects by location and category"""
        cache_key = self._generate_cache_key("prospects", location, category)
        return await self.get(cache_key)
    
    async def cache_prospects(self, location: str, category: str, prospects: List[Dict], ttl: int = 1800):
        """Cache prospects for 30 minutes by default"""
        cache_key = self._generate_cache_key("prospects", location, category)
        await self.set(cache_key, prospects, ttl=ttl)
    
    async def invalidate_prospects_cache(self, location: str = None, category: str = None):
        """Invalidate prospects cache"""
        if location and category:
            cache_key = self._generate_cache_key("prospects", location, category)
            await self.delete(cache_key)
        else:
            await self.delete_pattern("prospects:*")
    
    async def get_cached_pitch(self, business_name: str, industry: str) -> Optional[Dict]:
        """Get cached pitch"""
        cache_key = self._generate_cache_key("pitch", business_name, industry)
        return await self.get(cache_key)
    
    async def cache_pitch(self, business_name: str, industry: str, pitch: Dict, ttl: int = 3600):
        """Cache pitch for 1 hour by default"""
        cache_key = self._generate_cache_key("pitch", business_name, industry)
        await self.set(cache_key, pitch, ttl=ttl)
    
    async def get_cached_analytics(self, report_type: str, params: str) -> Optional[Dict]:
        """Get cached analytics report"""
        cache_key = self._generate_cache_key("analytics", report_type, params)
        return await self.get(cache_key)
    
    async def cache_analytics(self, report_type: str, params: str, data: Dict, ttl: int = 900):
        """Cache analytics for 15 minutes by default"""
        cache_key = self._generate_cache_key("analytics", report_type, params)
        await self.set(cache_key, data, ttl=ttl)
    
    async def get_user_session(self, session_id: str) -> Optional[Dict]:
        """Get cached user session"""
        cache_key = f"session:{session_id}"
        return await self.get(cache_key)
    
    async def cache_user_session(self, session_id: str, session_data: Dict, ttl: int = 86400):
        """Cache user session for 24 hours by default"""
        cache_key = f"session:{session_id}"
        await self.set(cache_key, session_data, ttl=ttl)
    
    async def invalidate_user_session(self, session_id: str):
        """Invalidate user session"""
        cache_key = f"session:{session_id}"
        await self.delete(cache_key)
    
    async def get_rate_limit(self, identifier: str) -> Optional[int]:
        """Get current rate limit count"""
        cache_key = f"ratelimit:{identifier}"
        return await self.get(cache_key)
    
    async def increment_rate_limit(self, identifier: str, window_seconds: int = 60) -> Optional[int]:
        """Increment rate limit counter"""
        cache_key = f"ratelimit:{identifier}"
        
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return None
        
        try:
            pipe = self._redis.pipeline()
            pipe.incr(cache_key)
            pipe.expire(cache_key, window_seconds)
            results = await pipe.execute()
            return results[0]
        except Exception as e:
            logger.error(f"Redis rate limit error: {str(e)}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            return {"status": "disconnected", "error": "Unable to connect to Redis"}
        
        try:
            info = await self._redis.info()
            return {
                "status": "healthy",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

# Global cache instance
cache = RedisCache()
