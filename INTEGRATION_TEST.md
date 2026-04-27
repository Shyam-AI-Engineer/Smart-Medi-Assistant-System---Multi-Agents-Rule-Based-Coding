# Frontend-Backend Integration Testing Guide

## Prerequisites
- Backend running on `http://localhost:8000`
- Frontend will run on `http://localhost:3000`
- Database populated with schema

---

## Test 1: Authentication Flow

### 1a. Register New User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "integration-test@example.com",
    "password": "TestPassword123",
    "full_name": "Integration Test User"
  }'
```

**Expected Response (201):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user_id": "uuid",
  "email": "integration-test@example.com",
  "role": "patient"
}
```

**Save:** `ACCESS_TOKEN` and `USER_ID` for next steps

---

### 1b. Verify Login Works
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "integration-test@example.com",
    "password": "TestPassword123"
  }'
```

**Expected Response (200):**
Same as register response.

---

## Test 2: Patient Profile Loading

### 2a. Get Patient Profile
```bash
curl -X GET http://localhost:8000/api/v1/patients/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Expected Response (200):**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "date_of_birth": null,
  "medical_history": null,
  "allergies": null,
  "current_medications": null,
  "emergency_contact": null
}
```

**Save:** `PATIENT_ID` (the `id` field)

---

### 2b. Update Patient Profile (Optional)
```bash
curl -X PUT http://localhost:8000/api/v1/patients/me \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "allergies": "Penicillin",
    "medical_history": "History of hypertension"
  }'
```

**Expected Response (200):**
Updated patient object with new values.

---

## Test 3: Vitals Analysis (Stateless)

### 3a. Analyze Vitals WITHOUT Storage
```bash
curl -X POST http://localhost:8000/api/v1/vitals/analyze \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "heart_rate": 145,
    "blood_pressure_systolic": 160,
    "blood_pressure_diastolic": 100,
    "oxygen_saturation": 88,
    "temperature": 38.5
  }'
```

**Expected Response (200):**
```json
{
  "overall_status": "CRITICAL",
  "severity_level": 4,
  "vital_analyses": [
    {
      "vital_type": "heart_rate",
      "value": 145,
      "unit": "bpm",
      "status": "ELEVATED",
      "severity": "HIGH",
      "normal_range": {"min": 60, "max": 100},
      "explanation": "...",
      "recommendation": "...",
      "confidence": 0.95
    }
    // ... more vitals
  ],
  "critical_findings": ["..."],
  "overall_assessment": "...",
  "recommendations": ["..."],
  "should_escalate_to_triage": true,
  "confidence_score": 0.92,
  "agent_used": "monitoring",
  "tokens_used": 1240,
  "timestamp": "2026-04-26T12:45:00",
  "disclaimer": "...",
  "response": "...",
  "error": false
}
```

---

## Test 4: Vitals Storage & Analysis

### 4a. Store Vitals WITH Analysis & Trend
```bash
curl -X POST http://localhost:8000/api/v1/vitals \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "heart_rate": 120,
    "blood_pressure_systolic": 140,
    "blood_pressure_diastolic": 90,
    "oxygen_saturation": 95,
    "temperature": 37.2,
    "notes": "After exercise"
  }'
```

**Expected Response (201):**
```json
{
  "record": {
    "id": "uuid",
    "patient_id": "uuid",
    "heart_rate": 120,
    "blood_pressure_systolic": 140,
    "blood_pressure_diastolic": 90,
    "oxygen_saturation": 95,
    "temperature": 37.2,
    "notes": "After exercise",
    "anomaly_detected": false,
    "anomaly_score": null,
    "created_at": "2026-04-26T12:45:00"
  },
  "analysis": {
    "overall_status": "MODERATE",
    "severity_level": 2,
    // ... rest of analysis object
  },
  "trend": "STABLE"
}
```

---

## Test 5: Vitals History

### 5a. Fetch Vitals History
```bash
curl -X GET "http://localhost:8000/api/v1/vitals/$PATIENT_ID?limit=10&offset=0" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Expected Response (200):**
```json
{
  "patient_id": "uuid",
  "items": [
    {
      "id": "uuid",
      "heart_rate": 120,
      // ... vital fields
      "created_at": "2026-04-26T12:45:00"
    }
    // ... more records (newest first)
  ],
  "total": 5,
  "limit": 10,
  "offset": 0,
  "has_next": false
}
```

---

## Test 6: Chat/AI Messaging

### 6a. Send Chat Message
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does a heart rate of 145 mean?"
  }'
```

**Expected Response (200):**
```json
{
  "response": "Based on medical guidelines, a heart rate of 145 bpm is elevated...",
  "sources": [
    {
      "file": "cardiology_guidelines.pdf",
      "relevance": "0.94%",
      "source_type": "pdf",
      "preview": "..."
    }
  ],
  "agent_used": "clinical",
  "confidence_score": 0.92,
  "tokens_used": 1240,
  "context_documents_used": 3,
  "error": false
}
```

---

## Test 7: Error Handling & Edge Cases

### 7a. Invalid Credentials
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "wrong@example.com", "password": "wrong"}'
```

**Expected Response (401):**
```json
{"detail": "Invalid email or password"}
```

---

### 7b. Missing Required Fields (Validation)
```bash
curl -X POST http://localhost:8000/api/v1/vitals/analyze \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Response (422):**
```json
{"detail": "At least one vital sign measurement is required"}
```

---

### 7c. Unauthorized Access (No Token)
```bash
curl -X GET http://localhost:8000/api/v1/patients/me
```

**Expected Response (403):**
```json
{"detail": "Not authenticated"}
```

---

### 7d. Invalid Token
```bash
curl -X GET http://localhost:8000/api/v1/patients/me \
  -H "Authorization: Bearer invalid-token-xyz"
```

**Expected Response (401):**
```json
{"detail": "Invalid or expired token"}
```

---

## Test 8: Concurrent Requests & Rate Limits

### 8a. Multiple Consecutive Vitals Submissions
Submit 10 vitals in quick succession, verify all return 201 with unique IDs.

### 8b. Check for Rate Limiting (Future Test)
Once rate limiting is implemented, verify 429 status after 10 requests/minute.

---

## Frontend Integration Test Checklist

- [ ] User can register and get JWT token
- [ ] JWT token is stored in localStorage
- [ ] User is redirected to dashboard after login
- [ ] Patient profile loads on dashboard
- [ ] User can submit vitals
- [ ] Vitals analysis displays correctly
- [ ] Trend indicator shows STABLE/IMPROVING/WORSENING
- [ ] Chat message is sent and response displays
- [ ] Error messages are user-friendly (not raw API errors)
- [ ] Logout clears token and redirects to login
- [ ] Protected routes redirect to login when not authenticated
- [ ] API errors (503, 500) show graceful fallback messages

---

## Expected Data Flow

```
User Login
  ↓ (POST /auth/login)
JWT Token + User Info stored in localStorage
  ↓ (GET /patients/me)
Patient ID retrieved
  ↓ (POST /vitals or /vitals/analyze)
Vitals analyzed by MonitoringAgent
  ↓
Results displayed with sources & confidence
  ↓ (POST /chat)
Chat message sent to AI
  ↓
Response from Clinical/RAG agent displayed
```

---

## Debugging Tips

**Token Issues:**
- Check localStorage in browser DevTools
- Verify token in JWT.io debugger
- Check Authorization header format: `Bearer <token>`

**CORS Issues:**
- Verify frontend URL in CORS allow_origins (should include http://localhost:3000)
- Check browser console Network tab for CORS errors

**API Response Issues:**
- Use `curl -v` for verbose output to see headers
- Check backend logs for error messages
- Verify Content-Type headers are application/json

**Patient Profile Missing:**
- Ensure user registered with role=patient
- Check if patient record was created on signup
- Verify patient_id exists in database

---

## Verification Commands

```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS headers
curl -i -X OPTIONS http://localhost:8000/api/v1/auth/login

# Test full auth flow (one-liner)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test'$(date +%s)'@ex.com", "password": "Password123!", "full_name": "Test"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4) && \
curl -s http://localhost:8000/api/v1/patients/me -H "Authorization: Bearer $TOKEN"
```

