# Example integration for your other Flask apps
# This shows how cash-forecast-analyzer or other apps will use the admin API

from fabric_admin_client import FabricAdminClient
from functools import wraps
from flask import session, abort

# Initialize the client (do this once at app startup)
admin_client = FabricAdminClient(
    base_url="http://localhost:5000",  # Change to your Azure URL when deployed
    api_key="your-api-key-here",  # Get from environment variable
    app_id=1  # Your app's ID in the APP_ADMINS table
)

# -----------------
# Pattern 1: Simple Admin Check
# -----------------
def require_admin_simple():
    """Decorator to protect routes - simple version"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_email = session.get('user', {}).get('email')
            if not user_email:
                abort(401, "Not logged in")
            
            # Check if user is admin for this app
            if not admin_client.is_admin(user_email):
                abort(403, "You must be an admin to access this page")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# -----------------
# Pattern 2: Admin Check with Caching (Recommended)
# -----------------
from datetime import datetime, timedelta

class AdminCache:
    """Simple cache to avoid hitting the API on every request"""
    def __init__(self, ttl_minutes=5):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def is_admin(self, email):
        # Check cache first
        if email in self.cache:
            cached_value, timestamp = self.cache[email]
            if datetime.now() - timestamp < self.ttl:
                return cached_value
        
        # Cache miss - check API
        is_admin = admin_client.is_admin(email)
        self.cache[email] = (is_admin, datetime.now())
        return is_admin
    
    def clear(self):
        self.cache = {}

# Create cache instance
admin_cache = AdminCache(ttl_minutes=5)

def require_admin():
    """Decorator to protect routes - with caching"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_email = session.get('user', {}).get('email')
            if not user_email:
                abort(401, "Not logged in")
            
            # Check cached admin status
            if not admin_cache.is_admin(user_email):
                abort(403, "You must be an admin to access this page")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# -----------------
# Pattern 3: Display Admin Info in Templates
# -----------------
def inject_admin_status():
    """Template context processor to show admin status"""
    user_email = session.get('user', {}).get('email')
    if user_email:
        return {
            'is_admin': admin_cache.is_admin(user_email),
            'admin_manage_url': 'http://localhost:5000'  # Link to admin management UI
        }
    return {'is_admin': False}


# -----------------
# Usage Examples in Your Routes
# -----------------
from flask import Flask, render_template

app = Flask(__name__)

# Register the context processor
app.context_processor(inject_admin_status)

@app.route('/admin/settings')
@require_admin()
def admin_settings():
    """Only admins can access this"""
    return render_template('admin_settings.html')


@app.route('/dashboard')
def dashboard():
    """Everyone can access, but admins see extra features"""
    user_email = session.get('user', {}).get('email')
    is_admin = admin_cache.is_admin(user_email) if user_email else False
    
    return render_template('dashboard.html', is_admin=is_admin)


# -----------------
# Example: Managing Admins from Your App
# -----------------
@app.route('/admin/users')
@require_admin()
def admin_users():
    """Show all admins for this app"""
    try:
        # Get all admins for this specific app
        admins = admin_client.get_admins_by_app()
        return render_template('admin_users.html', admins=admins)
    except Exception as e:
        return f"Error loading admins: {str(e)}", 500


@app.route('/admin/add', methods=['POST'])
@require_admin()
def add_admin():
    """Add a new admin (requires existing admin to add)"""
    from flask import request
    
    new_email = request.form.get('email')
    notes = request.form.get('notes', '')
    
    try:
        admin_client.create_admin({
            'APP_ID': 1,  # Cash Forecast app ID
            'USER_EMAIL': new_email,
            'Notes': notes,
            'IsActive': True
        })
        return "Admin added successfully", 200
    except Exception as e:
        return f"Error adding admin: {str(e)}", 500


# -----------------
# Environment Configuration
# -----------------
# In your .env file for each app:
# ADMIN_API_URL=http://localhost:5000  # or https://your-app.azurewebsites.net
# ADMIN_API_KEY=your-api-key-here
# ADMIN_APP_ID=1  # Your app's ID in the APP_ADMINS table

# Then initialize like this:
# admin_client = FabricAdminClient(
#     base_url=os.getenv('ADMIN_API_URL'),
#     api_key=os.getenv('ADMIN_API_KEY'),
#     app_id=int(os.getenv('ADMIN_APP_ID'))
# )
