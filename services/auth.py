"""
Azure AD Authentication Module
Handles user authentication via Microsoft identity platform
"""

import os
import logging
from functools import wraps
from flask import redirect, url_for, session, request
import msal

logger = logging.getLogger(__name__)


class AzureADAuth:
    """Handle Azure AD OAuth authentication flows"""
    
    def __init__(self, app=None):
        self.app = app
        self.client_id = os.environ.get('AZURE_AD_CLIENT_ID', '')
        self.client_secret = os.environ.get('AZURE_AD_CLIENT_SECRET', '')
        self.tenant_id = os.environ.get('AZURE_AD_TENANT_ID', '')
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        self.redirect_uri = os.environ.get('AZURE_AD_REDIRECT_URI', 
                                          'http://localhost:5000/auth/callback')
        
        # Request basic user profile scopes
        self.scopes = ["User.Read"]
    
    def get_msal_app(self, cache=None):
        """Create MSAL confidential client application with token cache"""
        if cache is None:
            cache = msal.SerializableTokenCache()
            if 'token_cache' in session:
                cache.deserialize(session['token_cache'])
        
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
            token_cache=cache
        )
        
        # Save cache back to session if it changed
        if cache.has_state_changed:
            session['token_cache'] = cache.serialize()
        
        return app
    
    def get_auth_url(self):
        """Generate Azure AD authorization URL"""
        msal_app = self.get_msal_app()
        
        auth_url = msal_app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        return auth_url
    
    def acquire_token_by_auth_code(self, code):
        """Exchange authorization code for access token"""
        cache = msal.SerializableTokenCache()
        if 'token_cache' in session:
            cache.deserialize(session['token_cache'])
            
        msal_app = self.get_msal_app(cache=cache)
        
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        # Save cache after token acquisition
        if cache.has_state_changed:
            session['token_cache'] = cache.serialize()
        
        if "error" in result:
            logger.error(f"Token acquisition error: {result.get('error_description')}")
            return None
        
        return result


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_user():
    """Get current logged-in user from session"""
    return session.get('user')
