#!/usr/bin/env python3
"""Test chat endpoint via HTTP (like frontend does)."""
import requests
import sys
import os

# Fix Windows console encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Get an access token first
print("Step 1: Login...")
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "patient@example.com",
        "password": "password123"
    }
)

if login_response.status_code != 200:
    print(f"[FAIL] Login failed: {login_response.status_code}")
    print(login_response.text)
    sys.exit(1)

access_token = login_response.json()["access_token"]
user_id = login_response.json()["user_id"]
print(f"[OK] Logged in, token: {access_token[:20]}...")
print(f"[OK] User ID: {user_id}")

# Get patient_id from database
from app.extensions import SessionLocal
from app.models import Patient
db = SessionLocal()
patient = db.query(Patient).filter_by(user_id=user_id).first()
if not patient:
    print("[FAIL] Patient profile not found")
    sys.exit(1)
patient_id = patient.id
print(f"[OK] Patient ID: {patient_id}")
db.close()

# Send chat message
print("\nStep 2: Send chat message...")
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={"message": "What is hypertension?"},
    headers=headers,
)

print(f"Status: {response.status_code}")
print(f"Response size: {len(response.text)} bytes")
print(f"\nResponse JSON:")
data = response.json()
for key, value in data.items():
    if isinstance(value, str) and len(value) > 150:
        preview = value[:150].encode('utf-8', errors='ignore').decode('utf-8')
        print(f"  {key}: {preview}...")
    elif isinstance(value, str):
        safe_value = value.encode('utf-8', errors='ignore').decode('utf-8')
        print(f"  {key}: {safe_value}")
    elif isinstance(value, list) and len(value) > 0:
        print(f"  {key}: {len(value)} items")
    else:
        try:
            print(f"  {key}: {value}")
        except:
            print(f"  {key}: <data>")

# Check database
print("\nStep 3: Check if message was saved to database...")
from app.extensions import SessionLocal
from app.models import ChatHistory

db = SessionLocal()
saved = db.query(ChatHistory).filter_by(patient_id=patient_id).order_by(ChatHistory.created_at.desc()).first()
if saved:
    print(f"[OK] Last message in DB: {saved.user_message[:60]}")
    print(f"  Created: {saved.created_at}")
else:
    print("[FAIL] No messages in database for this patient")
db.close()
