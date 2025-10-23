"""
Direct test of login without Postman
"""
import requests
import json

BASE_URL = "https://ubiquitous-winner-74r594j6xgwcx6w5-8000.app.github.dev"

print("=" * 60)
print("Testing Login Endpoint")
print("=" * 60)

login_data = {
    "username": "admin",
    "password": "admin123"
}

print(f"\n📝 Request URL: {BASE_URL}/auth/login")
print(f"📝 Request Data: {json.dumps(login_data, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"\n📊 Status Code: {response.status_code}")
    print(f"📊 Response Headers: {dict(response.headers)}")
    print(f"📊 Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"\n✅ Login successful!")
        print(f"🔑 Token: {token[:50]}...")
    else:
        print(f"\n❌ Login failed with status {response.status_code}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ Request failed: {e}")
except Exception as e:
    print(f"\n❌ Error: {e}")
