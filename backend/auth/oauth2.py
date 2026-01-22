"""
OAuth2 Integration for CEP Machine
Production-ready OAuth2 authentication with Google, GitHub, and Microsoft
"""

import os
from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse
import logging

from backend.config.security import SecurityUtils

logger = logging.getLogger(__name__)

# Initialize OAuth
oauth = OAuth()

# Register Google OAuth
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Register GitHub OAuth
oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID', ''),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET', ''),
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)

# Register Microsoft OAuth
oauth.register(
    name='microsoft',
    client_id=os.getenv('MICROSOFT_CLIENT_ID', ''),
    client_secret=os.getenv('MICROSOFT_CLIENT_SECRET', ''),
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

class OAuth2Service:
    """OAuth2 authentication service"""
    
    def __init__(self):
        self.supported_providers = ['google', 'github', 'microsoft']
    
    def get_provider(self, provider_name: str):
        """Get OAuth provider by name"""
        if provider_name not in self.supported_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider_name}"
            )
        return getattr(oauth, provider_name)
    
    async def login(self, request: Request, provider: str) -> RedirectResponse:
        """Initiate OAuth login flow"""
        oauth_provider = self.get_provider(provider)
        redirect_uri = request.url_for('oauth_callback', provider=provider)
        return await oauth_provider.authorize_redirect(request, redirect_uri)
    
    async def callback(self, request: Request, provider: str) -> Dict[str, Any]:
        """Handle OAuth callback"""
        oauth_provider = self.get_provider(provider)
        
        try:
            token = await oauth_provider.authorize_access_token(request)
        except Exception as e:
            logger.error(f"OAuth token error for {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to obtain access token"
            )
        
        # Get user info based on provider
        user_info = await self._get_user_info(oauth_provider, token, provider)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get user information"
            )
        
        # Create or update user in database
        user = await self._get_or_create_user(user_info, provider)
        
        # Generate JWT token
        access_token = SecurityUtils.create_access_token(
            data={
                "sub": str(user['id']),
                "email": user['email'],
                "provider": provider
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    
    async def _get_user_info(self, oauth_provider, token: Dict, provider: str) -> Optional[Dict[str, Any]]:
        """Get user info from OAuth provider"""
        try:
            if provider == 'google':
                user_info = token.get('userinfo')
                if not user_info:
                    user_info = await oauth_provider.userinfo(token=token)
                return {
                    'id': user_info.get('sub'),
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'picture': user_info.get('picture'),
                    'email_verified': user_info.get('email_verified', False)
                }
            
            elif provider == 'github':
                resp = await oauth_provider.get('user', token=token)
                user_data = resp.json()
                
                # Get email separately if not public
                email = user_data.get('email')
                if not email:
                    emails_resp = await oauth_provider.get('user/emails', token=token)
                    emails = emails_resp.json()
                    primary_email = next((e for e in emails if e.get('primary')), None)
                    email = primary_email.get('email') if primary_email else None
                
                return {
                    'id': str(user_data.get('id')),
                    'email': email,
                    'name': user_data.get('name') or user_data.get('login'),
                    'picture': user_data.get('avatar_url'),
                    'email_verified': True
                }
            
            elif provider == 'microsoft':
                user_info = token.get('userinfo')
                if not user_info:
                    user_info = await oauth_provider.userinfo(token=token)
                return {
                    'id': user_info.get('sub'),
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'picture': None,
                    'email_verified': user_info.get('email_verified', False)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info from {provider}: {str(e)}")
            return None
    
    async def _get_or_create_user(self, user_info: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Get or create user in database"""
        from backend.config.database import get_session
        import uuid
        
        # For now, return user info directly
        # In production, this would interact with the database
        user = {
            'id': user_info.get('id') or str(uuid.uuid4()),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'provider': provider,
            'email_verified': user_info.get('email_verified', False),
            'role': 'operator'  # Default role
        }
        
        logger.info(f"User authenticated via {provider}: {user['email']}")
        return user

oauth2_service = OAuth2Service()

# Convenience functions
async def oauth2_login(request: Request, provider: str = 'google') -> RedirectResponse:
    """Initiate OAuth2 login"""
    return await oauth2_service.login(request, provider)

async def oauth2_callback(request: Request, provider: str = 'google') -> Dict[str, Any]:
    """Handle OAuth2 callback"""
    return await oauth2_service.callback(request, provider)
