"""
Quick end-to-end auth test to verify signup + login flow.
"""
import requests, json, time

BASE = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json", "Origin": "http://localhost:5173"}
EMAIL = f"testfix_{int(time.time())}@example.com"
PASSWORD = "TestFix123"

print(f"=== AUTH FLOW TEST ===")
print(f"Email: {EMAIL}\n")

# --- SIGNUP ---
print("1) POST /auth/signup ...")
r = requests.post(f"{BASE}/auth/signup",
                  json={"email": EMAIL, "password": PASSWORD},
                  headers=HEADERS)
print(f"   Status : {r.status_code}")
print(f"   Body   : {r.json()}")
print(f"   CORS   : Access-Control-Allow-Origin = {r.headers.get('Access-Control-Allow-Origin', 'MISSING')}")
assert r.status_code == 201, f"Signup failed: {r.status_code}"
print("   ✅ Signup OK\n")

# --- LOGIN ---
print("2) POST /auth/login ...")
r2 = requests.post(f"{BASE}/auth/login",
                   json={"email": EMAIL, "password": PASSWORD},
                   headers=HEADERS)
print(f"   Status : {r2.status_code}")
body = r2.json()
print(f"   Body keys: {list(body.keys())}")
print(f"   CORS   : Access-Control-Allow-Origin = {r2.headers.get('Access-Control-Allow-Origin', 'MISSING')}")

if r2.status_code == 200:
    print(f"   access_token  : {body.get('access_token','MISSING')[:30]}...")
    print(f"   refresh_token : {body.get('refresh_token','MISSING')[:20]}...")
    print(f"   expires_in    : {body.get('expires_in')}")
    print(f"   user          : {body.get('user')}")
    print("   ✅ Login OK\n")
else:
    print(f"   ❌ Login FAILED: {body}")

# --- TOKEN REFRESH ---
if r2.status_code == 200:
    print("3) POST /auth/refresh ...")
    r3 = requests.post(f"{BASE}/auth/refresh",
                       json={"refresh_token": body["refresh_token"]},
                       headers=HEADERS)
    print(f"   Status : {r3.status_code}")
    print(f"   Body   : {r3.json()}")
    if r3.status_code == 200:
        print("   ✅ Token refresh OK\n")
    else:
        print("   ❌ Token refresh FAILED\n")

print("=== DONE ===")
