# Fabric SQL Admin API Documentation

## Overview

This API provides centralized access to the APP_ADMINS table in Fabric SQL. Apps can call this API to manage their administrative users instead of building their own database connections.

## Authentication

All API requests require an API key passed in the `X-API-Key` header.

```http
X-API-Key: your-app-api-key-here
```

## Base URL

- **Local Development**: `http://localhost:5000`
- **Production**: `https://your-app-name.azurewebsites.net`

## Endpoints

### Get All Admins

Get all admin records from the database.

```http
GET /api/admins
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "ID": 129,
      "ADMIN_EMAIL": "user@example.com",
      "ADMIN_TYPE": "super",
      "APP_ID": 34,
      "APP_NAME": "My Application",
      "DATE_CREATED": "2026-05-20T10:30:00"
    }
  ]
}
```

### Get Single Admin

Get a specific admin by ID.

```http
GET /api/admins/{id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "ID": 129,
    "ADMIN_EMAIL": "user@example.com",
    "ADMIN_TYPE": "super",
    "APP_ID": 34,
    "APP_NAME": "My Application",
    "DATE_CREATED": "2026-05-20T10:30:00"
  }
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error": "Admin not found"
}
```

### Create Admin

Create a new admin record.

```http
POST /api/admins
Content-Type: application/json

{
  "admin_email": "newadmin@example.com",
  "admin_type": "admin",
  "app_id": 34,
  "app_name": "My Application"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 150
  }
}
```

### Update Admin

Update an existing admin record.

```http
PUT /api/admins/{id}
Content-Type: application/json

{
  "admin_email": "updated@example.com",
  "admin_type": "super",
  "app_id": 34,
  "app_name": "My Application"
}
```

**Response:**
```json
{
  "success": true
}
```

### Delete Admin

Delete an admin record.

```http
DELETE /api/admins/{id}
```

**Response:**
```json
{
  "success": true
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "success": false,
  "error": "Authentication required. Provide X-API-Key header."
}
```

### 400 Bad Request
```json
{
  "success": false,
  "error": "Missing required field: admin_email"
}
```

### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Database connection error: ..."
}
```

## Configuration

### For the Admin API Service

Add API keys to `.env`:

```env
# API Keys for apps (format: APP_NAME:key,APP_NAME2:key2)
API_KEYS=CashForecastApp:cf-key-2026-secure,SurpriseApp:surprise-key-2026,MyApp:myapp-key-2026

# Allowed origins for CORS (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5001,https://myapp.azurewebsites.net
```

### For Apps Calling the API

Add to your app's `.env`:

```env
# Fabric Admin API Configuration
ADMIN_API_URL=http://localhost:5000
ADMIN_API_KEY=your-app-api-key-here
```

## Client Library

Use the provided `fabric_admin_client.py` in your Flask apps:

```python
from fabric_admin_client import FabricAdminClient

# Initialize once in your app
admin_client = FabricAdminClient(
    api_url=os.environ.get('ADMIN_API_URL'),
    api_key=os.environ.get('ADMIN_API_KEY')
)

# Use in your routes
@app.route('/admin/list')
@login_required
def list_admins():
    admins = admin_client.get_admins_by_app(app_id=34)
    return render_template('admins.html', admins=admins)
```

## Common Patterns

### Check if User is Admin

```python
def is_admin(user_email, app_id):
    try:
        admins = admin_client.get_admins_by_app(app_id)
        return any(
            admin['ADMIN_EMAIL'].lower() == user_email.lower() 
            for admin in admins
        )
    except:
        return False
```

### Admin Required Decorator

```python
from functools import wraps
from flask import session, abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_email = session.get('user', {}).get('email')
        if not user_email or not is_admin(user_email, app_id=34):
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/sensitive-action')
@login_required
@admin_required
def sensitive_action():
    # Only admins can access this
    pass
```

### Filter Admins by Type

```python
admins = admin_client.get_admins_by_app(app_id=34)
super_admins = [a for a in admins if a['ADMIN_TYPE'] == 'super']
regular_admins = [a for a in admins if a['ADMIN_TYPE'] == 'admin']
```

## Rate Limiting

Currently no rate limiting. Consider adding in production:
- Per API key limits
- IP-based throttling
- Azure API Management

## Security Best Practices

1. **API Keys**: Generate strong, unique keys for each app
2. **HTTPS Only**: Always use HTTPS in production
3. **CORS**: Restrict allowed origins to known apps
4. **Logging**: Log all API access for audit trails
5. **Secrets**: Store API keys in Azure Key Vault in production

## Testing

Test the API with curl:

```bash
# Get all admins
curl -H "X-API-Key: your-key" http://localhost:5000/api/admins

# Create admin
curl -X POST \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"admin_email":"test@example.com","admin_type":"admin","app_id":34,"app_name":"Test"}' \
  http://localhost:5000/api/admins

# Update admin
curl -X PUT \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"admin_email":"updated@example.com","admin_type":"super","app_id":34,"app_name":"Test"}' \
  http://localhost:5000/api/admins/150

# Delete admin
curl -X DELETE \
  -H "X-API-Key: your-key" \
  http://localhost:5000/api/admins/150
```

## Support

For issues or questions, contact the platform team.
