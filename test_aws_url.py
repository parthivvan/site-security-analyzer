import requests

url = "https://us-east-1.console.aws.amazon.com/apprunner/home?region=us-east-1#/welcome"
api_url = "http://127.0.0.1:5000/scan"

# Assuming you don't actually need auth to trigger the validation (or if you do, we'll see a 401 instead of 400 invalid URL)
print("Testing URL:", url)
res = requests.post(api_url, json={"url": url})
print(f"Status: {res.status_code}")
print(f"Response: {res.text}")
