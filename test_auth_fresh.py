import requests
import string
import random

BASE_URL = "http://localhost:5000/auth"
email = f"test_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}@gmail.com"
password = "Testpass@123"

print(f"Using email: {email}")

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
