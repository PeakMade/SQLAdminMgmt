"""
Test Fabric SQL Connection
Quick script to verify connectivity and permissions
"""

import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from services.fabric_db import FabricDatabase

def test_connection():
    """Test basic connectivity"""
    print("\n" + "="*60)
    print("FABRIC SQL CONNECTION TEST")
    print("="*60)
    
    print(f"\nServer: {os.environ.get('FABRIC_SERVER')}")
    print(f"Database: {os.environ.get('FABRIC_DATABASE')}")
    print(f"Client ID: {os.environ.get('FABRIC_CLIENT_ID')[:20]}...")
    
    db = FabricDatabase()
    
    print("\n1. Testing authentication and connection...")
    try:
        if db.test_connection():
            print("   ✓ Connection successful!")
        else:
            print("   ✗ Connection failed")
            return False
    except Exception as e:
        print(f"   ✗ Connection error: {str(e)}")
        return False
    
    print("\n2. Testing query access to APP_ADMINS table...")
    try:
        admins = db.get_all_admins()
        print(f"   ✓ Successfully queried APP_ADMINS table")
        print(f"   ✓ Found {len(admins)} records")
        
        if admins:
            print("\n   Sample record:")
            admin = admins[0]
            print(f"   - ID: {admin.get('ID')}")
            print(f"   - Email: {admin.get('ADMIN_EMAIL')}")
            print(f"   - Type: {admin.get('ADMIN_TYPE')}")
            print(f"   - App: {admin.get('APP_NAME')} (ID: {admin.get('APP_ID')})")
            
    except Exception as e:
        print(f"   ✗ Query error: {str(e)}")
        return False
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    return True

if __name__ == '__main__':
    test_connection()
