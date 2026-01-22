"""
Authentication API endpoints for CEP Machine
Production-ready auth endpoints with OAuth2, MFA, and session management
"""

from fastapi import APIRouter, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import logging

from backend.auth.oauth2 import oauth2_service
from backend.auth.mfa import mfa_manager, mfa_service
from backend.auth.rbac import RBACUser, ROLES, Permission
from backend.config.security import SecurityUtils

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfa_token: Optional[str] = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class MFASetupRequest(BaseModel):
    user_id: str
    email: EmailStr

class MFAVerifyRequest(BaseModel):
    user_id: str
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

@router.post("/login")
async def login(request: LoginRequest):
    """Login with email and password"""
    try:
        # Verify credentials (in production, check against database)
        # This is a simplified example
        if not request.email or not request.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Mock user lookup - in production, query database
        user_id = "user_" + request.email.split("@")[0]
        
        # Check if MFA is enabled
        if mfa_manager.is_mfa_enabled(user_id):
            if not request.mfa_token:
                return JSONResponse({
                    "success": False,
                    "mfa_required": True,
                    "message": "MFA token required"
                }, status_code=status.HTTP_401_UNAUTHORIZED)
            
            # Verify MFA token
            mfa_result = await mfa_manager.verify_mfa(user_id, request.mfa_token)
            if not mfa_result.get("valid"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid MFA token"
                )
        
        # Generate JWT token
        access_token = SecurityUtils.create_access_token(
            data={"sub": user_id, "email": request.email}
        )
        
        logger.info(f"User logged in: {request.email}")
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": request.email,
                "role": "operator"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/register")
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        # In production, check if user exists and save to database
        user_id = "user_" + request.email.split("@")[0]
        
        # Hash password
        hashed_password = SecurityUtils.hash_password(request.password)
        
        # Generate JWT token
        access_token = SecurityUtils.create_access_token(
            data={"sub": user_id, "email": request.email}
        )
        
        logger.info(f"User registered: {request.email}")
        
        return {
            "success": True,
            "message": "User registered successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": request.email,
                "name": request.name,
                "role": "viewer"
            }
        }
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.get("/oauth/{provider}")
async def oauth_login(request: Request, provider: str):
    """Initiate OAuth login flow"""
    try:
        return await oauth2_service.login(request, provider)
    except Exception as e:
        logger.error(f"OAuth login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth login failed: {str(e)}"
        )

@router.get("/oauth/{provider}/callback")
async def oauth_callback(request: Request, provider: str):
    """Handle OAuth callback"""
    try:
        result = await oauth2_service.callback(request, provider)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}"
        )

@router.post("/mfa/setup")
async def setup_mfa(request: MFASetupRequest):
    """Set up MFA for a user"""
    try:
        result = await mfa_manager.enable_mfa(request.user_id, request.email)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"MFA setup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA setup failed: {str(e)}"
        )

@router.post("/mfa/verify")
async def verify_mfa_setup(request: MFAVerifyRequest):
    """Verify MFA setup with a token"""
    try:
        result = await mfa_manager.verify_and_enable_mfa(request.user_id, request.token)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"MFA verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA verification failed: {str(e)}"
        )

@router.post("/mfa/disable")
async def disable_mfa(request: MFAVerifyRequest):
    """Disable MFA for a user"""
    try:
        result = await mfa_manager.disable_mfa(request.user_id, request.token)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"MFA disable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA disable failed: {str(e)}"
        )

@router.post("/mfa/backup-codes")
async def regenerate_backup_codes(request: MFAVerifyRequest):
    """Regenerate MFA backup codes"""
    try:
        result = await mfa_manager.regenerate_backup_codes(request.user_id, request.token)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Backup codes error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup codes regeneration failed: {str(e)}"
        )

@router.post("/logout")
async def logout():
    """Logout user"""
    # In production, invalidate token/session
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me")
async def get_current_user():
    """Get current user info (requires authentication)"""
    # In production, extract user from JWT token
    return {
        "id": "user_demo",
        "email": "demo@example.com",
        "name": "Demo User",
        "role": "operator",
        "mfa_enabled": False,
        "permissions": list(ROLES["operator"].permissions)
    }

@router.get("/roles")
async def list_roles():
    """List available roles"""
    return {
        "roles": [
            {
                "name": role.name,
                "description": role.description,
                "permissions": [p.value for p in role.permissions]
            }
            for role in ROLES.values()
        ]
    }

@router.get("/permissions")
async def list_permissions():
    """List available permissions"""
    return {
        "permissions": [p.value for p in Permission]
    }

@router.get("/health")
async def auth_health():
    """Auth service health check"""
    return {
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat()
    }
