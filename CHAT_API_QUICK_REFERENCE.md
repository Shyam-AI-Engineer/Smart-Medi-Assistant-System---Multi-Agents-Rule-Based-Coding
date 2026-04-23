# Chat API - Quick Reference

> Copy/paste examples for testing endpoints

---

## Setup

**1. Start backend:**
```bash
cd backend
source venv/Scripts/activate  # Windows: bash
pip install -r requirements.txt
python -m uvicorn app:app --reload
```

**2. Set environment variables** (in `.env`):
```bash
EURI_API_KEY=sk-proj-your-actual-key
JWT_SECRET_KEY=your-secret-min-32-chars
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smart_medi_dev
```

**3. Database ready** (PostgreSQL running)

---

## Health Check (No Auth Required)

```bash
# Check if API is running
curl http://localhost:8000/

# Check service health
curl http://localhost:8000/health

# Check chat service specifically
curl http://localhost:8000/api/v1/chat/health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "euri": true,
    "faiss": true,
    "database": true
  }
}
```

---

## Authentication (Phase 2b - Not Yet Implemented)

For now, you'll need a valid JWT token. Here's how to generate one:

```python
# In Python shell:
from app.middleware.auth_middleware import create_access_token

token = create_access_token(
    user_id="patient-123",
    email="patient@example.com",
    role="patient"
)
print(token)
```

Save the token in your terminal:
```bash
JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicGF0aWVudC0xMjMiLCJlbWFpbCI6InBhdGllbnRAZXhhbXBsZS5jb20iLCJyb2xlIjoicGF0aWVudCIsImV4cCI6MTcxNzAwMDAwMH0.xxxxx"
```

---

## Send Message to AI

**Endpoint:** `POST /api/v1/chat`

**Simple request:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a headache and fever for 2 days"
  }'
```

**With pretty output:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a headache and fever for 2 days"
  }' | python -m json.tool
```

**Example Request JSON:**
```json
{
  "message": "I have chest pain. Should I be worried?"
}
```

**Example Response JSON:**
```json
{
  "response": "Chest pain can have multiple causes and requires proper evaluation. Possible causes include:\n\n1. **Cardiac causes**: Heart disease, angina\n2. **Pulmonary causes**: Pneumonia, pulmonary embolism\n3. **Musculoskeletal**: Muscle strain, rib inflammation\n4. **Gastrointestinal**: Acid reflux, gastritis\n\n⚠️ **SEEK IMMEDIATE MEDICAL ATTENTION IF**:\n- Severe chest pressure with shortness of breath\n- Pain radiating to arm or jaw\n- Dizziness or fainting\n\nThis is for informational purposes only. Contact emergency services for severe symptoms.",
  "sources": [
    {
      "file": "chest_pain_diagnosis.pdf",
      "relevance": "94%",
      "source_type": "pdf",
      "preview": "Differential diagnosis of chest pain including cardiac and non-cardiac causes..."
    },
    {
      "file": "cardiology_guidelines.txt",
      "relevance": "89%",
      "source_type": "text",
      "preview": "Clinical guidelines for chest pain evaluation in primary care..."
    }
  ],
  "agent_used": "clinical",
  "confidence_score": 0.92,
  "tokens_used": 1240,
  "context_documents_used": 2,
  "timestamp": "2026-04-23T10:30:45.123456",
  "error": false
}
```

---

## Get Chat History

**Endpoint:** `GET /api/v1/chat/history`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/chat/history?limit=20&offset=0" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json"
```

**Example Response:**
```json
{
  "items": [
    {
      "id": "chat-uuid-1",
      "user_message": "I have a headache",
      "ai_response": "Based on medical guidelines...",
      "agent_used": "clinical",
      "confidence_score": 0.92,
      "created_at": "2026-04-23T10:30:45Z"
    },
    {
      "id": "chat-uuid-2",
      "user_message": "What should I do?",
      "ai_response": "You should...",
      "agent_used": "clinical",
      "confidence_score": 0.89,
      "created_at": "2026-04-23T10:31:12Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0,
  "has_next": true
}
```

---

## Error Examples

**Missing JWT token:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Response: 403 Forbidden
# {"detail": "Not authenticated"}
```

**Invalid JWT token:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer invalid-token" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Response: 401 Unauthorized
# {"detail": "Invalid token"}
```

**Message too long (>1000 chars):**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "'"$(python3 -c 'print("x" * 1001)')"'"}'

# Response: 400 Bad Request
# {"detail": "ensure this value has at most 1000 characters"}
```

**Empty message:**
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": ""}'

# Response: 400 Bad Request
# {"detail": "ensure this value has at least 1 characters"}
```

**Service unavailable (Euri API down):**
```bash
# Response: 503 Service Unavailable
{
  "detail": "AI service is temporarily unavailable. Please try again."
}
```

---

## Postman Collection

Import this into Postman:

```json
{
  "info": {
    "name": "Smart Medi Assistant API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/api/v1/chat/health"
      }
    },
    {
      "name": "Send Message",
      "request": {
        "method": "POST",
        "url": "http://localhost:8000/api/v1/chat",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{jwt_token}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"message\": \"I have a headache\"}"
        }
      }
    },
    {
      "name": "Get History",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/api/v1/chat/history?limit=20&offset=0",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{jwt_token}}"
          }
        ]
      }
    }
  ]
}
```

---

## Python Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Generate JWT token (see authentication section above)
token = "eyJhbGc..."

# Send message
response = requests.post(
    f"{BASE_URL}/api/v1/chat",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    },
    json={"message": "I have a headache"}
)

print(response.status_code)
print(json.dumps(response.json(), indent=2))

# Get history
response = requests.get(
    f"{BASE_URL}/api/v1/chat/history?limit=20",
    headers={"Authorization": f"Bearer {token}"}
)
print(json.dumps(response.json(), indent=2))
```

---

## Test Data

**Add sample medical documents to FAISS:**

```python
from app.agents.clinical_agent import ClinicalAgent

agent = ClinicalAgent()

# Add a document
result = agent.ingest_medical_document(
    content="""
    Headache Management Guidelines:
    - Common causes: tension, migraine, sinus, viral infection
    - Treatment: hydration, rest, over-the-counter pain relief
    - Seek care if: severe, persistent, accompanied by fever/vision changes
    """,
    source_type="text",
    source_name="headache_guidelines.txt",
)

print(f"Added document: {result}")
```

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Missing JWT | Add `-H "Authorization: Bearer $JWT_TOKEN"` |
| 503 Service Unavailable | EURI_API_KEY not set | Set `EURI_API_KEY` in `.env` |
| 404 Patient not found | Patient profile missing | Create patient profile first (Phase 2b) |
| FAISS index empty | No documents ingested | Use `ClinicalAgent.ingest_medical_document()` |
| Slow responses (>10s) | Network issues | Check internet, try again |

---

## OpenAPI Documentation

Once backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These auto-generate from Pydantic schemas and route docstrings.

---

## What's Next?

✅ Chat routes complete
➡️ Phase 2b: Create auth routes (register, login)
➡️ Phase 2c: Create patient routes (profile, vitals)
➡️ Phase 3: Build frontend (Next.js chat UI)
