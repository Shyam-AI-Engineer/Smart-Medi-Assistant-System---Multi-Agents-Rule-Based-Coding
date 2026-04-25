# MonitoringAgent - Quick Start Guide

## In 60 Seconds

The **MonitoringAgent** analyzes vital signs and detects health anomalies with automatic escalation to emergency care.

### What It Does
```
Input:  {"heart_rate": 145, "oxygen_saturation": 88}
        ↓
        Rule-based severity check + LLM explanation
        ↓
Output: {
          "overall_status": "HIGH",
          "should_escalate_to_triage": true,
          "recommendations": ["Contact doctor immediately"]
        }
```

---

## Usage in 3 Lines

```python
from app.agents.monitoring_agent import get_monitoring_agent

agent = get_monitoring_agent()
response = agent.analyze_vitals({"heart_rate": 120, "blood_pressure_systolic": 145})
print(response["overall_status"])  # "MODERATE"
```

---

## Vital Sign Thresholds

| Vital | Critical Low | Normal Range | Critical High |
|-------|--------------|--------------|---------------|
| Heart Rate | <40 | 60-100 | >140 |
| SBP (mmHg) | <90 | 100-120 | >180 |
| DBP (mmHg) | <50 | 60-80 | >120 |
| SpO2 (%) | <85 | ≥95 | 100 |
| Temperature (°C) | <34 | 36.5-37.5 | >40 |
| RR (br/min) | <8 | 12-20 | >30 |

---

## Severity Levels

🚨 **CRITICAL** (Level 4) - Emergency  
⚠️ **HIGH** (Level 3) - Urgent  
⚡ **MODERATE** (Level 2) - Monitor  
✅ **NORMAL** (Level 1) - Healthy  

---

## Response Format

```json
{
  "overall_status": "HIGH|MODERATE|NORMAL|CRITICAL",
  "severity_level": 1-4,
  "vital_analyses": [
    {
      "vital_type": "heart_rate",
      "value": 120,
      "status": "ELEVATED",
      "severity": "MODERATE",
      "recommendation": "Monitor and report to doctor"
    }
  ],
  "should_escalate_to_triage": true/false,
  "confidence_score": 0.93,
  "response": "Patient-friendly message"
}
```

---

## Integration in ChatService

```python
# Vitals extracted from message automatically
vitals = service._extract_vitals_from_message(
    "My heart rate is 145 and I feel dizzy"
)
# Returns: {"heart_rate": 145}

# Sent to monitoring agent
response = service.monitoring_agent.analyze_vitals(vitals)
```

---

## Orchestrator Routing

**Vitals are routed automatically!**

```
Message: "My blood pressure is 155/95"
    ↓
Keyword detected: "blood pressure"
    ↓
Routes to: monitoring_agent (confidence: 0.98)
    ↓
Extracts vitals and analyzes
```

**Vital Keywords** (triggers monitoring agent):
- heart rate, pulse, HR
- blood pressure, BP
- oxygen, SpO2, O2
- temperature, fever, temp
- respiratory rate, breathing
- vitals

---

## Critical Escalation

```python
response = agent.analyze_vitals({
    "heart_rate": 160,
    "oxygen_saturation": 82
})

if response["should_escalate_to_triage"]:
    # Route to triage agent for emergency assessment
    # Show emergency action buttons to user
    # Recommend calling 911
```

---

## Vital Extraction Patterns

```
"My heart rate is 120" → heart_rate: 120
"BP 140/90" → systolic: 140, diastolic: 90
"Fever of 38.5°C" → temperature: 38.5
"Oxygen at 94" → oxygen_saturation: 94
"Breathing 24 times per minute" → respiratory_rate: 24
```

---

## Test It

```bash
cd backend
python test_monitoring_agent.py
```

**Expected:** All 6 test scenarios pass with correct severity levels

---

## Common Queries

**Patient:** "Is my heart rate of 92 normal?"  
**Agent:** NORMAL status, healthy range, continue monitoring

**Patient:** "My temperature is 39.5°C"  
**Agent:** HIGH status, high fever, contact doctor immediately

**Patient:** "HR 155, can't breathe, oxygen 82"  
**Agent:** CRITICAL status, escalate to triage, recommend 911

---

## For Developers

### To Add a New Vital
1. Add to `VITAL_THRESHOLDS` dict in `monitoring_agent.py`
2. Add extraction pattern to `_extract_vitals_from_message()`
3. Add test case
4. Add to documentation

### To Change Thresholds
Edit `VITAL_THRESHOLDS` dictionary in `monitoring_agent.py`:
```python
VITAL_THRESHOLDS = {
    "heart_rate": {
        "critical_low": 40,
        "normal_min": 60,
        "normal_max": 100,
        "critical_high": 140,
    },
    # ... other vitals
}
```

### To Extend with Context
```python
# Agent already supports patient_info
response = agent.analyze_vitals(
    vitals,
    patient_info={
        "age": 75,
        "medical_history": "Heart disease"
    }
)
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `monitoring_agent.py` | Core engine |
| `base_agent.py` | Abstract parent class |
| `orchestrator.py` | Routing (vital keywords) |
| `chat_service.py` | Integration & extraction |
| `test_monitoring_agent.py` | Test suite |
| `MONITORING_AGENT.md` | Full documentation |

---

## Typical Flow

```
1. Frontend: "My heart rate is 120"
     ↓
2. API: POST /api/v1/chat
     ↓
3. Orchestrator: "vital keywords detected" → monitoring_agent
     ↓
4. ChatService: Extract vitals {heart_rate: 120}
     ↓
5. MonitoringAgent: Compare to thresholds → severity MODERATE
     ↓
6. Response: {
     status: "MODERATE",
     recommendation: "Monitor and report to doctor",
     escalate: false
   }
     ↓
7. Frontend: Display with moderate warning badge
```

---

## Key Features

✅ Rule-based thresholds (fast, deterministic)  
✅ LLM explanations (patient education)  
✅ Automatic keyword routing  
✅ Critical escalation detection  
✅ Patient context awareness  
✅ Type-safe Python (type hints everywhere)  
✅ Comprehensive logging  
✅ Graceful error handling  

---

## Next Steps

1. **Test**: Run `test_monitoring_agent.py`
2. **Deploy**: Merge to main branch
3. **API**: Create `/api/v1/vitals/analyze` endpoint
4. **UI**: Build vital sign dashboard
5. **Trends**: Add vital history & trend analysis
6. **Real-Time**: WebSocket monitoring for continuous tracking

---

**Quick Links:**
- Full Docs: `MONITORING_AGENT.md`
- Implementation Summary: `IMPLEMENTATION_SUMMARY.md`
- Tests: `test_monitoring_agent.py`
- Code: `app/agents/monitoring_agent.py`

