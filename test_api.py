"""
Quick test script to verify the API is working
Run this to test API authentication and endpoints
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
API_KEY = "your-api-key-here"  # Replace with actual key from .env
HEADERS = {"X-API-Key": API_KEY}

def test_api():
    print("Testing Fabric Admin API...")
    print("=" * 50)
    
    # Test 1: Get all admins
    print("\n1. Testing GET /api/admins (get all admins)")
    response = requests.get(f"{BASE_URL}/api/admins", headers=HEADERS)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            admins = result.get('data', [])
            print(f"   Found {len(admins)} admins")
            if admins:
                print(f"   First admin: {admins[0].get('ADMIN_EMAIL')} (App: {admins[0].get('APP_NAME')})")
        else:
            print(f"   API returned success=False: {result.get('error')}")
    else:
        print(f"   Error: {response.text}")
    
    # Test 2: Get specific admin
    if response.status_code == 200 and result.get('success') and result.get('data'):
        admins = result.get('data')
        admin_id = admins[0]['ID']
        print(f"\n2. Testing GET /api/admins/{admin_id} (get specific admin)")
        response = requests.get(f"{BASE_URL}/api/admins/{admin_id}", headers=HEADERS)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                admin = result.get('data')
                print(f"   Admin: {admin['ADMIN_EMAIL']} (App: {admin['APP_NAME']})")
            else:
                print(f"   API returned success=False: {result.get('error')}")
        else:
            print(f"   Error: {response.text}")
    
    # Test 3: Test without API key (should fail)
    print("\n3. Testing without API key (should return 401)")
    response = requests.get(f"{BASE_URL}/api/admins")
    print(f"   Status: {response.status_code}")
    print(f"   Message: {response.json().get('error', 'No error message')}")
    
    # Test 4: Test with wrong API key (should fail)
    print("\n4. Testing with wrong API key (should return 401)")
    wrong_headers = {"X-API-Key": "wrong-key-12345"}
    response = requests.get(f"{BASE_URL}/api/admins", headers=wrong_headers)
    print(f"   Status: {response.status_code}")
    print(f"   Message: {response.json().get('error', 'No error message')}")
    
    print("\n" + "=" * 50)
    print("API testing complete!")

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API.")
        print("Make sure the Flask app is running on http://localhost:5000")
    except Exception as e:
        print(f"ERROR: {str(e)}")
