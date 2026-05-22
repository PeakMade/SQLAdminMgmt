# Fabric SQL Admin API - Client Example
# How to call the API from another Flask app

import requests
import json

class FabricAdminClient:
    """
    Client for calling the Fabric SQL Admin API
    Use this in your apps to manage APP_ADMINS records
    """
    
    def __init__(self, api_url, api_key):
        """
        Initialize the client
        
        Args:
            api_url: Base URL of the admin API (e.g., http://localhost:5000 or https://your-app.azurewebsites.net)
            api_key: Your app's API key
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def get_all_admins(self):
        """Get all admin records"""
        response = requests.get(
            f'{self.api_url}/api/admins',
            headers=self.headers
        )
        response.raise_for_status()
        result = response.json()
        # Return the data array from the API response
        if result.get('success'):
            return result.get('data', [])
        else:
            raise Exception(result.get('error', 'Unknown error'))
    
    def get_admin(self, admin_id):
        """Get a specific admin by ID"""
        response = requests.get(
            f'{self.api_url}/api/admins/{admin_id}',
            headers=self.headers
        )
        response.raise_for_status()
        result = response.json()
        # Return the data object from the API response
        if result.get('success'):
            return result.get('data')
        else:
            raise Exception(result.get('error', 'Unknown error'))
    
    def get_admins_by_app(self, app_id=None):
        """Get all admins for a specific app (defaults to the app_id set in constructor)"""
        if app_id is None:
            app_id = self.app_id
        
        all_admins = self.get_all_admins()
        return [admin for admin in all_admins if admin['APP_ID'] == app_id]
    
    def is_admin(self, user_email, app_id=None):
        """Check if a user is an admin for this app"""
        if app_id is None:
            app_id = self.app_id
        
        try:
            admins = self.get_admins_by_app(app_id)
            return any(
                admin.get('ADMIN_EMAIL', '').lower() == user_email.lower() 
                and admin.get('IsActive', True)  # Default to True if not present
                for admin in admins
            )
        except Exception:
            return False
    
    def create_admin(self, admin_data):
        """
        Create a new admin record
        
        Args:
            admin_data: Dict with keys: admin_email, admin_type, app_id, app_name
        
        Returns:
            Created admin record ID
        """
        response = requests.post(
            f'{self.api_url}/api/admins',
            headers=self.headers,
            json=admin_data
        )
        response.raise_for_status()
        result = response.json()
        if result.get('success'):
            return result.get('id')
        else:
            raise Exception(result.get('error', 'Unknown error'))
    
    def update_admin(self, admin_id, admin_data):
        """
        Update an existing admin record
        
        Args:
            admin_id: The ID of the admin to update
            admin_data: Dict with keys: admin_email, admin_type, app_id, app_name
        
        Returns:
            True if successful
        """
        response = requests.put(
            f'{self.api_url}/api/admins/{admin_id}',
            headers=self.headers,
            json=admin_data
        )
        response.raise_for_status()
        result = response.json()
        if result.get('success'):
            return True
        else:
            raise Exception(result.get('error', 'Unknown error'))
    
    def delete_admin(self, admin_id):
        """
        Delete an admin record
        
        Args:
            admin_id: The ID of the admin to delete
        
        Returns:
            True if successful
        """
        response = requests.delete(
            f'{self.api_url}/api/admins/{admin_id}',
            headers=self.headers
        )
        response.raise_for_status()
        result = response.json()
        if result.get('success'):
            return True
        else:
            raise Exception(result.get('error', 'Unknown error'))


# ============================================================================
# EXAMPLE USAGE IN YOUR FLASK APP
# ============================================================================

# In your app's __init__ or config:
# from fabric_admin_client import FabricAdminClient
# admin_client = FabricAdminClient(
#     api_url='http://localhost:5000',  # or production URL
#     api_key='your-app-api-key-here'
# )

# Then in your app's routes:

# Example 1: Get all admins for your app
# @app.route('/admin/list')
# @login_required
# def list_admins():
#     try:
#         my_admins = admin_client.get_admins_by_app(app_id=34)  # Your app's ID
#         return render_template('admins.html', admins=my_admins)
#     except Exception as e:
#         flash(f'Error loading admins: {str(e)}', 'error')
#         return redirect(url_for('index'))

# Example 2: Add an admin
# @app.route('/admin/add', methods=['POST'])
# @login_required
# def add_admin():
#     try:
#         result = admin_client.create_admin(
#             admin_email=request.form['email'],
#             admin_type='admin',
#             app_id=34,  # Your app's ID
#             app_name='My Application'
#         )
#         flash('Admin added successfully', 'success')
#         return redirect(url_for('list_admins'))
#     except Exception as e:
#         flash(f'Error adding admin: {str(e)}', 'error')
#         return redirect(url_for('list_admins'))

# Example 3: Check if current user is an admin
# def is_admin(user_email, app_id):
#     try:
#         admins = admin_client.get_admins_by_app(app_id)
#         return any(admin['ADMIN_EMAIL'].lower() == user_email.lower() for admin in admins)
#     except:
#         return False

# Example 4: Decorator to require admin access
# from functools import wraps
# from flask import session, abort
# 
# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         user_email = session.get('user', {}).get('email')
#         if not user_email or not is_admin(user_email, app_id=34):
#             abort(403)  # Forbidden
#         return f(*args, **kwargs)
#     return decorated_function


if __name__ == '__main__':
    # Test the client
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Initialize client
    client = FabricAdminClient(
        api_url=os.environ.get('ADMIN_API_URL', 'http://localhost:5000'),
        api_key=os.environ.get('ADMIN_API_KEY', 'test-key')
    )
    
    print("Testing Fabric Admin API Client")
    print("=" * 60)
    
    try:
        # Test: Get all admins
        print("\n1. Getting all admins...")
        result = client.get_all_admins()
        if result['success']:
            print(f"   ✓ Found {len(result['data'])} admins")
        
        # Test: Get admins for specific app
        print("\n2. Getting admins for app ID 34...")
        admins = client.get_admins_by_app(34)
        print(f"   ✓ Found {len(admins)} admins for this app")
        
        print("\n" + "=" * 60)
        print("✓ API client working correctly!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n✗ API Error: {str(e)}")
        print("\nMake sure:")
        print("  1. The admin API server is running")
        print("  2. Your API key is configured in .env")
        print("  3. The API URL is correct")
