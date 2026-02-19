import requests
import json

# Test credentials
EMAIL = "debugtest456@example.com"
PASSWORD = "Password123"

print("="*60)
print("COMPREHENSIVE LOGIN DEBUG TEST")
print("="*60)
print(f"\nTest Email: {EMAIL}")
print(f"Test Password: {PASSWORD}")
print(f"Password Length: {len(PASSWORD)}")
print(f"Password repr: {repr(PASSWORD)}")
print()

# Step 1: Signup
print("STEP 1: Creating account via /auth/signup")
print("-"*60)
signup_payload = {"email": EMAIL, "password": PASSWORD}
print(f"Signup payload: {json.dumps(signup_payload, indent=2)}")

try:
    r1 = requests.post('http://127.0.0.1:5000/auth/signup', json=signup_payload)
    print(f"Status Code: {r1.status_code}")
    print(f"Response: {r1.json()}")
    if r1.status_code == 201:
        print("✅ Signup SUCCESS")
    else:
        print("❌ Signup FAILED")
        print("Cannot continue test")
        exit(1)
except Exception as e:
    print(f"❌ Signup ERROR: {e}")
    exit(1)

print()

# Step 2: Immediate login with exact same credentials
print("STEP 2: Login immediately with EXACT same credentials")
print("-"*60)
login_payload = {"email": EMAIL, "password": PASSWORD}
print(f"Login payload: {json.dumps(login_payload, indent=2)}")
print(f"Same email? {signup_payload['email'] == login_payload['email']}")
print(f"Same password? {signup_payload['password'] == login_payload['password']}")
print(f"Email bytes equal? {signup_payload['email'].encode() == login_payload['email'].encode()}")
print(f"Password bytes equal? {signup_payload['password'].encode() == login_payload['password'].encode()}")

try:
    r2 = requests.post('http://127.0.0.1:5000/auth/login', json=login_payload)
    print(f"Status Code: {r2.status_code}")
    
    if r2.status_code == 200:
        data = r2.json()
        print("✅ Login SUCCESS")
        print(f"Access token received: {data.get('access_token', '')[:50]}...")
        print(f"User ID: {data.get('user', {}).get('id')}")
        print(f"User Email: {data.get('user', {}).get('email')}")
    else:
        print("❌ Login FAILED")
        print(f"Error response: {r2.text}")
        
except Exception as e:
    print(f"❌ Login ERROR: {e}")

print()
print("="*60)
print("CHECK THE FLASK LOGS for:")
print("  - Signup attempt log showing password length and repr")
print("  - Login attempt log showing password length and repr")
print("  - Password check failed log (if login failed)")
print("="*60)
