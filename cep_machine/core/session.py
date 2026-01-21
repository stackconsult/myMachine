"""
Session management for CEP Machine
Uses DragonflyDB for persistent session storage
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

from .cache import get_cache, session_cache_key

logger = logging.getLogger(__name__)

@dataclass
class SessionData:
    """Session data structure"""
    session_id: str
    user_id: Optional[str] = None
    user_type: str = "anonymous"  # anonymous, admin, client
    data: Dict[str, Any] = None
    created_at: datetime = None
    last_accessed: datetime = None
    expires_at: datetime = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_accessed is None:
            self.last_accessed = datetime.utcnow()
        if self.expires_at is None:
            self.expires_at = datetime.utcnow() + timedelta(hours=24)

class SessionManager:
    """Manages user sessions using DragonflyDB cache"""
    
    def __init__(self, default_ttl: int = 86400):  # 24 hours default
        self.default_ttl = default_ttl
        self._cache = None
    
    async def get_cache(self):
        """Get cache instance"""
        if not self._cache:
            self._cache = await get_cache()
        return self._cache
    
    async def create_session(
        self,
        user_id: Optional[str] = None,
        user_type: str = "anonymous",
        data: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> SessionData:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        
        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            user_type=user_type,
            data=data or {},
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
        )
        
        # Store in cache
        cache = await self.get_cache()
        cache_key = session_cache_key(session_id)
        await cache.set(cache_key, asdict(session), ttl or self.default_ttl)
        
        logger.info(f"Created session {session_id} for user {user_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        cache = await self.get_cache()
        cache_key = session_cache_key(session_id)
        
        session_data = await cache.get(cache_key)
        if not session_data:
            return None
        
        # Check if expired
        if isinstance(session_data, dict):
            expires_at = session_data.get('expires_at')
            if expires_at:
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at)
                if datetime.utcnow() > expires_at:
                    await self.delete_session(session_id)
                    return None
            
            # Update last accessed
            session_data['last_accessed'] = datetime.utcnow().isoformat()
            await cache.set(cache_key, session_data)
            
            # Convert to SessionData
            session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
            session_data['last_accessed'] = datetime.fromisoformat(session_data['last_accessed'])
            session_data['expires_at'] = datetime.fromisoformat(session_data['expires_at'])
            
            return SessionData(**session_data)
        
        return None
    
    async def update_session(
        self,
        session_id: str,
        data: Optional[Dict[str, Any]] = None,
        extend_ttl: Optional[bool] = True,
    ) -> Optional[SessionData]:
        """Update session data"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        if data:
            session.data.update(data)
        
        if extend_ttl:
            session.expires_at = datetime.utcnow() + timedelta(seconds=self.default_ttl)
        
        session.last_accessed = datetime.utcnow()
        
        # Store updated session
        cache = await self.get_cache()
        cache_key = session_cache_key(session_id)
        await cache.set(cache_key, asdict(session), self.default_ttl)
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        cache = await self.get_cache()
        cache_key = session_cache_key(session_id)
        
        result = await cache.delete(cache_key)
        
        if result:
            logger.info(f"Deleted session {session_id}")
        
        return result
    
    async def list_active_sessions(self, user_type: Optional[str] = None) -> List[SessionData]:
        """List all active sessions (admin function)"""
        # This would require scanning all session keys
        # For now, return empty list - implement if needed
        return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        # This would require scanning all session keys
        # For now, return 0 - implement if needed
        return 0
    
    async def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """Extend session TTL"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
        session.last_accessed = datetime.utcnow()
        
        cache = await self.get_cache()
        cache_key = session_cache_key(session_id)
        await cache.set(cache_key, asdict(session), ttl or self.default_ttl)
        
        return True

# Rate limiting implementation
class RateLimiter:
    """Rate limiting using DragonflyDB"""
    
    def __init__(self):
        self._cache = None
    
    async def get_cache(self):
        """Get cache instance"""
        if not self._cache:
            self._cache = await get_cache()
        return self._cache
    
    async def is_allowed(
        self,
        identifier: str,  # IP address, user ID, etc.
        limit: int,  # Number of requests allowed
        window: int,  # Time window in seconds
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed based on rate limit
        
        Returns:
            (allowed, info) where info contains:
            - remaining: remaining requests
            - reset_time: when limit resets
            - current: current request count
        """
        cache = await self.get_cache()
        
        # Create sliding window key
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window)
        key = f"rate_limit:{identifier}:{window}"
        
        # Get current requests in window
        current = await cache.get(key) or 0
        
        if current >= limit:
            # Rate limit exceeded
            reset_time = now + timedelta(seconds=window)
            return False, {
                "remaining": 0,
                "reset_time": reset_time.isoformat(),
                "current": current,
                "limit": limit,
                "window": window
            }
        
        # Increment counter
        new_count = await cache.increment(key)
        
        # Set TTL if this is the first request
        if new_count == 1:
            await cache.set(key, new_count, window)
        
        # Calculate remaining
        remaining = max(0, limit - new_count)
        reset_time = now + timedelta(seconds=window)
        
        return True, {
            "remaining": remaining,
            "reset_time": reset_time.isoformat(),
            "current": new_count,
            "limit": limit,
            "window": window
        }
    
    async def check_multiple_limits(
        self,
        identifier: str,
        limits: List[tuple[int, int]],  # List of (limit, window) tuples
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check multiple rate limits
        
        Args:
            identifier: IP address, user ID, etc.
            limits: List of (limit, window) tuples
        
        Returns:
            (allowed, info) - allowed only if ALL limits pass
        """
        for limit, window in limits:
            allowed, info = await self.is_allowed(identifier, limit, window)
            if not allowed:
                return False, info
        
        return True, {"all_limits_passed": True, "limits_checked": len(limits)}

# Global instances
session_manager = SessionManager()
rate_limiter = RateLimiter()

# Decorators for session and rate limiting
def require_session(func):
    """Decorator to require valid session"""
    async def wrapper(*args, **kwargs):
        # Extract session_id from kwargs or headers
        session_id = kwargs.get('session_id')
        if not session_id:
            raise ValueError("Session ID required")
        
        session = await session_manager.get_session(session_id)
        if not session:
            raise ValueError("Invalid or expired session")
        
        # Add session to kwargs
        kwargs['session'] = session
        
        return await func(*args, **kwargs)
    return wrapper

def rate_limit(limit: int, window: int, identifier_key: str = "ip"):
    """Decorator for rate limiting"""
    async def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get identifier
            identifier = kwargs.get(identifier_key)
            if not identifier:
                raise ValueError(f"Identifier '{identifier_key}' required for rate limiting")
            
            # Check rate limit
            allowed, info = await rate_limiter.is_allowed(identifier, limit, window)
            
            if not allowed:
                raise Exception(f"Rate limit exceeded: {limit} requests per {window}s")
            
            # Add rate limit info to kwargs
            kwargs['rate_limit_info'] = info
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
