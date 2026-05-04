#!/bin/bash

API_URL="http://localhost:8000/api/v1"

echo "=========================================="
echo "Testing Appointment File Download Flow"
echo "=========================================="

# 1. Register test user
echo -e "\n[1] Registering test user..."
USER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_download@example.com",
    "password": "TestPassword123",
    "full_name": "Test User"
  }')

TOKEN=$(echo "$USER_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
if [ -z "$TOKEN" ]; then
  echo "❌ Failed to register: $USER_RESPONSE"
  exit 1
fi
echo "✓ Registered. Token: ${TOKEN:0:20}..."

# 2. Create appointment with file
echo -e "\n[2] Creating appointment with file attachment..."
APPT_RESPONSE=$(curl -s -X POST "$API_URL/appointments/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "reason=Test appointment" \
  -F "preferred_date=2026-05-15" \
  -F "preferred_time_slot=10:00 AM" \
  -F "attachment=@/tmp/test_file.txt" 2>&1)

APPT_ID=$(echo "$APPT_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
ATTACHMENT_PATH=$(echo "$APPT_RESPONSE" | grep -o '"attachment_path":"[^"]*"' | cut -d'"' -f4)

if [ -z "$APPT_ID" ]; then
  echo "❌ Failed to create appointment: $APPT_RESPONSE"
  exit 1
fi
echo "✓ Created appointment: $APPT_ID"
echo "  Attachment path: $ATTACHMENT_PATH"

# 3. Download file
echo -e "\n[3] Downloading attachment..."
DOWNLOAD_RESPONSE=$(curl -s -i -X GET "$API_URL/appointments/files/$APPT_ID/$ATTACHMENT_PATH" \
  -H "Authorization: Bearer $TOKEN" 2>&1)

HTTP_CODE=$(echo "$DOWNLOAD_RESPONSE" | head -1)
if echo "$HTTP_CODE" | grep -q "200"; then
  echo "✓ Download successful (HTTP 200)"
else
  echo "❌ Download failed: $HTTP_CODE"
  echo "$DOWNLOAD_RESPONSE" | head -10
fi

echo -e "\n=========================================="
echo "Test complete!"
echo "=========================================="
