import requests

BASE_URL = "http://localhost:5000/auth"
email = "test123@gmail.com"
password = "Testpass@123"

# 1. Try Signup
print("Testing Signup...")
res = requests.post(f"{BASE_URL}/signup", json={"email": email, "password": password})
print(f"Status: {res.status_code}")
print(f"Response: {res.text}")

# 2. Try Login
print("\nTesting Login...")
res = requests.post(f"{BASE_URL}/login", json={"email": email, "password": password})
print(f"Status: {res.status_code}")
print(f"Response: {res.text}")
