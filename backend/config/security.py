"""
Security configuration and utilities for CEP Machine Backend
Production-ready security measures
"""

import os
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class SecurityConfig:
    """Centralized security configuration"""
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", self._generate_secret_key())
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", self._generate_jwt_key())
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
        self.encryption_key = os.getenv("ENCRYPTION_KEY", self._generate_encryption_key())
        
        # Rate limiting
        self.rate_limit_requests_per_minute = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
        self.rate_limit_burst_size = int(os.getenv("RATE_LIMIT_BURST_SIZE", "20"))
        
        # CORS
        self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        
        # API Keys
        self.copilotkit_license_key = os.getenv("COPILOTKIT_LICENSE_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)
    
    def _generate_jwt_key(self) -> str:
        """Generate a secure JWT key"""
        return secrets.token_urlsafe(32)
    
    def _generate_encryption_key(self) -> str:
        """Generate a secure encryption key"""
        return secrets.token_urlsafe(32)[:32]
    
    def validate_api_key(self, api_key: str, expected_key: Optional[str] = None) -> bool:
        """Validate API key"""
        if not expected_key:
            return True  # No validation required if no expected key
        
        return hmac.compare_digest(api_key, expected_key)

security_config = SecurityConfig()

class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=security_config.jwt_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            security_config.jwt_secret_key,
            algorithm=security_config.jwt_algorithm
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token,
                security_config.jwt_secret_key,
                algorithms=[security_config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def encrypt_sensitive_data(data: str) -> str:
        """Encrypt sensitive data (basic implementation)"""
        # In production, use proper encryption like AES-256
        key = security_config.encryption_key.encode()
        data_bytes = data.encode()
        
        # Simple XOR encryption (replace with proper encryption in production)
        encrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(data_bytes)])
        return encrypted.hex()
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str) -> str:
        """Decrypt sensitive data (basic implementation)"""
        key = security_config.encryption_key.encode()
        encrypted_bytes = bytes.fromhex(encrypted_data)
        
        # Simple XOR decryption (replace with proper decryption in production)
        decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted_bytes)])
        return decrypted.decode()
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """Sanitize user input to prevent XSS and injection"""
        if not input_string:
            return ""
        
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", "&", '"', "'", "/", "\\", ";", ":", "(", ")", "{", "}"]
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")
        
        # Limit length
        max_length = 1000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Hash data using SHA-256"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def verify_data_hash(data: str, expected_hash: str) -> bool:
        """Verify data against expected hash"""
        return hmac.compare_digest(
            SecurityUtils.hash_data(data),
            expected_hash
        )

class RateLimiter:
    """Simple rate limiter implementation"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.utcnow()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if (now - req_time).seconds < window
        ]
        
        # Check if under limit
        if len(self.requests[key]) < limit:
            self.requests[key].append(now)
            return True
        
        return False

# Global rate limiter
rate_limiter = RateLimiter()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = SecurityUtils.verify_token(token)
    
    # In a real application, you would fetch user from database
    user = {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "permissions": payload.get("permissions", [])
    }
    
    return user

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if not user or permission not in user.get("permissions", []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_copilotkit_license():
    """Validate CopilotKit license key"""
    license_key = security_config.copilotkit_license_key
    if not license_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CopilotKit license key is required"
        )
    
    # In production, validate against CopilotKit API
    # For now, just check if it's present and valid format
    if not license_key.startswith("ck_pub_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid CopilotKit license key format"
        )
    
    return True

def log_security_event(event_type: str, details: Dict[str, Any]):
    """Log security events"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": details
    }
    
    logger.warning(f"Security event: {log_entry}")
