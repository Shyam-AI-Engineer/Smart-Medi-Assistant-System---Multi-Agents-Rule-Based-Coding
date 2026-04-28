#!/usr/bin/env python3
"""Check login response structure."""
import requests
import json

login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "patient@example.com",
        "password": "password123"
    }
)

print(f"Status: {login_response.status_code}")
print(f"\nFull response:")
print(json.dumps(login_response.json(), indent=2))
