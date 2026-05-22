"""
API Authentication Middleware
Supports both web UI (session-based) and API calls (API key-based)
"""

import os
import logging
from functools import wraps
from flask import request, jsonify, session

logger = logging.getLogger(__name__)


def get_api_keys():
    """
    Load API keys from environment variable
    Format: APP_NAME1:key1,APP_NAME2:key2
    """
    api_keys_str = os.environ.get('API_KEYS', '')
    if not api_keys_str:
        return {}
    
    api_keys = {}
    for pair in api_keys_str.split(','):
        if ':' in pair:
            app_name, key = pair.split(':', 1)
            api_keys[key] = app_name.strip()
    
    return api_keys


def authenticate_request():
    """
    Authenticate request - supports both web UI (session) and API (key)
    Returns: (is_authenticated, auth_type, identifier)
    """
    # Check for session-based auth (web UI)
    if 'user' in session:
        return (True, 'session', session['user'].get('email', 'unknown'))
    
    # Check for API key auth
    api_key = request.headers.get('X-API-Key')
    if api_key:
        api_keys = get_api_keys()
        if api_key in api_keys:
            app_name = api_keys[api_key]
            logger.info(f"API request authenticated: {app_name}")
            return (True, 'api_key', app_name)
        else:
            logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
            return (False, None, None)
    
    # No authentication found
    return (False, None, None)


def api_or_login_required(f):
    """
    Decorator for routes that support both web UI and API access
    Web UI users must be logged in (session)
    API users must provide valid API key
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_authenticated, auth_type, identifier = authenticate_request()
        
        if not is_authenticated:
            # For API requests, return JSON error
            if request.headers.get('X-API-Key') or request.path.startswith('/api/'):
                return jsonify({
                    'success': False, 
                    'error': 'Authentication required. Provide X-API-Key header.'
                }), 401
            
            # For web UI requests, redirect to login
            from flask import redirect, url_for
            return redirect(url_for('login'))
        
        # Store auth info in request context for logging
        request.auth_type = auth_type
        request.auth_identifier = identifier
        
        return f(*args, **kwargs)
    
    return decorated_function


def api_key_required(f):
    """
    Decorator for API-only routes (requires API key)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key required. Provide X-API-Key header.'
            }), 401
        
        api_keys = get_api_keys()
        if api_key not in api_keys:
            logger.warning(f"Invalid API key attempted: {api_key[:10]}...")
            return jsonify({
                'success': False,
                'error': 'Invalid API key'
            }), 401
        
        app_name = api_keys[api_key]
        request.auth_identifier = app_name
        logger.info(f"API request authenticated: {app_name}")
        
        return f(*args, **kwargs)
    
    return decorated_function
