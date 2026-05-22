# Fabric Admin Service - Quick Start Guide

## Overview

You now have a **hybrid admin management service** that supports:
- **Web UI**: Manual admin management at http://localhost:5000 (or your Azure URL)
- **REST API**: Programmatic access for other Flask apps

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Fabric Admin Service                       │
│                  (http://localhost:5000)                     │
│                                                              │
│  ┌─────────────┐              ┌──────────────┐             │
│  │   Web UI    │              │  REST API    │             │
│  │  (Manual)   │              │ (Programmatic)│            │
│  │             │              │              │             │
│  │ - Login via │              │ - API Key    │             │
│  │   Azure AD  │              │   Auth       │             │
│  │ - CRUD      │              │ - JSON       │             │
│  │   Interface │              │   Responses  │             │
│  └─────────────┘              └──────────────┘             │
│         │                            │                      │
│         └────────────┬───────────────┘                      │
│                      │                                      │
│              ┌───────▼────────┐                             │
│              │  Fabric SQL DB │                             │
│              │  (APP_ADMINS)  │                             │
│              └────────────────┘                             │
└─────────────────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │                           │
┌───────▼────────┐         ┌────────▼───────┐
│ Cash Forecast  │         │ Other Flask    │
│ Analyzer       │         │ Apps           │
│                │         │                │
│ - Uses API Key │         │ - Uses API Key │
│ - Checks admins│         │ - Checks admins│
└────────────────┘         └────────────────┘
```

## For Your Other Flask Apps

### 1. Copy the Client Library

Copy [fabric_admin_client.py](fabric_admin_client.py) to your app's directory.

### 2. Configure Environment Variables

Add to your app's `.env`:
```env
ADMIN_API_URL=http://localhost:5000
ADMIN_API_KEY=your-api-key-here
ADMIN_APP_ID=1  # Your app's ID in the APP_ADMINS table
```

### 3. Initialize the Client

```python
import os
from fabric_admin_client import FabricAdminClient

# At app startup (e.g., in __init__.py or app.py)
admin_client = FabricAdminClient(
    base_url=os.getenv('ADMIN_API_URL'),
    api_key=os.getenv('ADMIN_API_KEY'),
    app_id=int(os.getenv('ADMIN_APP_ID'))
)
```

### 4. Protect Routes

```python
from functools import wraps
from flask import session, abort

def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_email = session.get('user', {}).get('email')
        if not user_email:
            abort(401, "Not logged in")
        
        if not admin_client.is_admin(user_email):
            abort(403, "Admin access required")
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/settings')
@require_admin
def admin_settings():
    """Only admins can access this"""
    return render_template('admin_settings.html')
```

### 5. Optional: Add Caching (Recommended)

```python
from datetime import datetime, timedelta

class AdminCache:
    def __init__(self, ttl_minutes=5):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def is_admin(self, email):
        # Check cache
        if email in self.cache:
            cached_value, timestamp = self.cache[email]
            if datetime.now() - timestamp < self.ttl:
                return cached_value
        
        # Cache miss - call API
        is_admin = admin_client.is_admin(email)
        self.cache[email] = (is_admin, datetime.now())
        return is_admin

admin_cache = AdminCache(ttl_minutes=5)

# Use admin_cache.is_admin() instead of admin_client.is_admin()
```

## API Keys

Current configured API keys (from `.env`):

| App Name | API Key |
|----------|---------|
| CASH_FORECAST | `your-api-key-here` |
| SHAREPOINT_APP | `another-api-key-here` |

### Generate New Keys

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to `.env`:
```env
API_KEYS=APP1:key1,APP2:key2,APP3:key3
```

## Testing

### Test the API

```bash
python test_api.py
```

### Test with curl

```bash
# Get all admins
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:5000/api/admins

# Get specific admin
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:5000/api/admins/1
```

## Files Reference

| File | Purpose |
|------|---------|
| [app.py](app.py) | Main Flask app with web UI and API routes |
| [services/fabric_db.py](services/fabric_db.py) | Fabric SQL database operations |
| [services/auth.py](services/auth.py) | Azure AD authentication (web UI) |
| [services/api_auth.py](services/api_auth.py) | API key authentication |
| [fabric_admin_client.py](fabric_admin_client.py) | **Client library for other apps** |
| [INTEGRATION_EXAMPLE.py](INTEGRATION_EXAMPLE.py) | Full integration examples |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete API reference |
| [test_api.py](test_api.py) | API test script |

## Common Patterns

### Check if user is admin in a route
```python
@app.route('/dashboard')
def dashboard():
    user_email = session.get('user', {}).get('email')
    is_admin = admin_cache.is_admin(user_email) if user_email else False
    return render_template('dashboard.html', is_admin=is_admin)
```

### Show admin status in templates
```python
# Add context processor
@app.context_processor
def inject_admin_status():
    user_email = session.get('user', {}).get('email')
    if user_email:
        return {'is_admin': admin_cache.is_admin(user_email)}
    return {'is_admin': False}
```

Then in template:
```html
{% if is_admin %}
  <a href="/admin/settings">Admin Settings</a>
{% endif %}
```

### Get all admins for your app
```python
@app.route('/admin/users')
@require_admin
def list_admins():
    admins = admin_client.get_admins_by_app()
    return render_template('admin_users.html', admins=admins)
```

## Deployment

When deploying to Azure:

1. **Update API URLs** in consuming apps' `.env`:
   ```env
   ADMIN_API_URL=https://your-admin-service.azurewebsites.net
   ```

2. **Configure CORS** if apps are on different domains (already configured in app.py)

3. **Secure API Keys**: Store in Azure Key Vault and reference in App Service configuration

4. **Database**: Fabric SQL connection works the same way (token-based auth)

## Next Steps

- [ ] Deploy to Azure App Service
- [ ] Update API URLs in consuming apps
- [ ] Add group-based authorization (currently any tenant user can login)
- [ ] Push to GitHub for CI/CD
- [ ] Consider adding role-based permissions beyond simple admin check

## Support

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.
See [INTEGRATION_EXAMPLE.py](INTEGRATION_EXAMPLE.py) for detailed code examples.
