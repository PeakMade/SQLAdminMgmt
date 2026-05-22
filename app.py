"""
Fabric SQL Admin Manager - Flask Application
Manages APP_ADMINS table in Microsoft Fabric SQL
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_session import Session
from flask_cors import CORS
import os
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from services.auth import AzureADAuth, login_required, get_user
from services.api_auth import api_or_login_required, api_key_required
from services.fabric_db import FabricDatabase

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(__file__), 'flask_session')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

# Configure CORS for API access
CORS(app, resources={
    r"/api/*": {
        "origins": os.environ.get('ALLOWED_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})

Session(app)

# Ensure session folder exists
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

# Initialize Azure AD authentication
azure_auth = AzureADAuth(app)

# Initialize Fabric database
fabric_db = FabricDatabase()


@app.route('/')
@login_required
def index():
    """Main page - display all admins"""
    try:
        admins = fabric_db.get_all_admins()
        return render_template('index.html', admins=admins, user=get_user())
    except Exception as e:
        flash(f'Error loading admins: {str(e)}', 'error')
        return render_template('index.html', admins=[], user=get_user())


@app.route('/api/admins', methods=['GET'])
@api_or_login_required
def get_admins():
    """API endpoint to get all admins (supports both web UI and API key auth)"""
    try:
        admins = fabric_db.get_all_admins()
        # Convert datetime objects to strings for JSON serialization
        for admin in admins:
            if admin.get('DATE_CREATED'):
                admin['DATE_CREATED'] = admin['DATE_CREATED'].isoformat()
        return jsonify({'success': True, 'data': admins})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admins/<int:admin_id>', methods=['GET'])
@api_or_login_required
def get_admin(admin_id):
    """API endpoint to get a single admin by ID (supports both web UI and API key auth)"""
    try:
        admin = fabric_db.get_admin_by_id(admin_id)
        if admin:
            if admin.get('DATE_CREATED'):
                admin['DATE_CREATED'] = admin['DATE_CREATED'].isoformat()
            return jsonify({'success': True, 'data': admin})
        else:
            return jsonify({'success': False, 'error': 'Admin not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admins', methods=['POST'])
@api_or_login_required
def create_admin():
    """API endpoint to create a new admin (supports both web UI and API key auth)"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['admin_email', 'admin_type', 'app_id', 'app_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        new_id = fabric_db.create_admin(
            admin_email=data['admin_email'],
            admin_type=data['admin_type'],
            app_id=int(data['app_id']),
            app_name=data['app_name']
        )
        
        return jsonify({'success': True, 'data': {'id': new_id}}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admins/<int:admin_id>', methods=['PUT'])
@api_or_login_required
def update_admin(admin_id):
    """API endpoint to update an existing admin (supports both web UI and API key auth)"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['admin_email', 'admin_type', 'app_id', 'app_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        success = fabric_db.update_admin(
            admin_id=admin_id,
            admin_email=data['admin_email'],
            admin_type=data['admin_type'],
            app_id=int(data['app_id']),
            app_name=data['app_name']
        )
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Admin not found or no changes made'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admins/<int:admin_id>', methods=['DELETE'])
@api_or_login_required
def delete_admin(admin_id):
    """API endpoint to delete an admin (supports both web UI and API key auth)"""
    try:
        success = fabric_db.delete_admin(admin_id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Admin not found'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/login')
def login():
    """Redirect to Azure AD login"""
    auth_url = azure_auth.get_auth_url()
    return redirect(auth_url)


@app.route('/auth/callback')
def auth_callback():
    """Handle Azure AD callback"""
    code = request.args.get('code')
    if not code:
        flash('Authentication failed: No authorization code received', 'error')
        return redirect(url_for('login'))
    
    result = azure_auth.acquire_token_by_auth_code(code)
    
    if result:
        # Store user info in session
        session['user'] = {
            'name': result.get('id_token_claims', {}).get('name', 'Unknown'),
            'email': result.get('id_token_claims', {}).get('preferred_username', 'Unknown'),
            'id': result.get('id_token_claims', {}).get('oid', 'Unknown')
        }
        return redirect(url_for('index'))
    else:
        flash('Authentication failed', 'error')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    """Log out the user"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/test-connection')
@login_required
def test_connection():
    """Test database connection"""
    try:
        if fabric_db.test_connection():
            return jsonify({'success': True, 'message': 'Database connection successful'})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
