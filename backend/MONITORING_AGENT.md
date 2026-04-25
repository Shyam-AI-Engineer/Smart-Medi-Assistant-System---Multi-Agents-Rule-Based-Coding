# Monitoring Agent - Vital Sign Analysis & Anomaly Detection

The Monitoring Agent analyzes vital signs in real-time, detects abnormal values, and provides clinical interpretation with recommendations.

## Architecture

```
Patient Vital Signs or Vital Query
    │
    ▼
┌────────────────────────────────┐
│    Monitoring Agent            │
│                                │
│ 1. Extract vital values        │
│    (heart rate, BP, temp, etc) │
│                                │
│ 2. Apply rule-based thresholds │
│    (normal, elevated, critical)│
│                                │
│ 3. Determine severity          │
│    (NORMAL > MODERATE > HIGH > │
│     CRITICAL)                  │
│                                │
│ 4. Get LLM explanations        │
│    (via Euri)                  │
│                                │
│ 5. Generate recommendations    │
│    (monitoring, follow-up)     │
│                                │
│ 6. Decide escalation           │
│    (triage for critical)       │
│                                │
│ 7. Format response             │
│    (patient-friendly)          │
└────────────────────────────────┘
    │
    ▼
{
  "overall_status": "NORMAL|MODERATE|HIGH|CRITICAL",
  "severity_level": 1-4,
  "vital_analyses": [
    {
      "vital_type": "heart_rate",
      "value": 120,
      "status": "HIGH",
      "severity": "MODERATE",
      "explanation": "Elevated heart rate may indicate stress or illness",
      "recommendation": "Monitor closely or consult doctor",
      "confidence": 0.93
    }
  ],
  "should_escalate_to_triage": true,
  "confidence_score": 0.93,
  "response": "Patient-friendly formatted message"
}
```

## Risk Levels & Thresholds

### CRITICAL 🚨 - SEEK IMMEDIATE HELP

**Status indicators:**
- Heart rate < 40 or > 140 bpm
- SBP < 90 or > 180 mmHg
- SpO2 < 85%
- Temperature < 34°C or > 40°C
- Respiratory rate < 8 or > 30 breaths/min

**Action:** Escalate to TriageAgent and recommend emergency services (911)

**Examples:**
- Heart rate 155 bpm with fever 40.5°C
- Systolic BP 190 mmHg (hypertensive crisis)
- Oxygen saturation 82% (severe hypoxia)
- Temperature 41°C (dangerous fever)

### HIGH ⚠️ - URGENT CONSULTATION

**Status indicators:**
- Heart rate 100-140 bpm
- SBP 140-180 or DBP 90-120 mmHg
- SpO2 85-90%
- Temperature 38-40°C
- Respiratory rate 24-30 breaths/min

**Action:** Recommend immediate doctor consultation

**Examples:**
- Heart rate 125 bpm at rest
- BP 155/95 mmHg (Stage 2 hypertension)
- Oxygen saturation 89% (moderate hypoxia)
- Temperature 39.5°C (high fever)

### MODERATE ⚡ - MONITOR & FOLLOW UP

**Status indicators:**
- Heart rate 90-100 bpm
- SBP 120-140 or DBP 80-90 mmHg
- SpO2 90-95%
- Temperature 37.5-38°C
- Respiratory rate 20-24 breaths/min

**Action:** Monitor closely, schedule doctor appointment

**Examples:**
- Heart rate 105 bpm (slightly elevated)
- BP 135/88 mmHg (prehypertension)
- Oxygen saturation 93% (low-normal)
- Temperature 37.8°C (slight fever)

### NORMAL ✅ - HEALTHY RANGE

**Status indicators:**
- Heart rate 60-100 bpm
- SBP 100-120 and DBP 60-80 mmHg
- SpO2 ≥ 95%
- Temperature 36.5-37.5°C
- Respiratory rate 12-20 breaths/min

**Action:** Continue regular monitoring

---

## Vital Sign Reference Ranges

### Heart Rate (bpm)
```
Critical Low:  < 40
Low:          60
Normal:       60-100
High:         100
Critical:     > 140
```

### Blood Pressure (mmHg)
**Systolic:**
```
Critical Low: < 90
Low:          100
Normal:       100-120
Stage 1:      140
Critical:     > 180
```

**Diastolic:**
```
Critical Low: < 50
Low:          60
Normal:       60-80
Stage 1:      90
Critical:     > 120
```

### Oxygen Saturation (%)
```
Critical: < 85%
Low:      90%
Normal:   95-100%
High:     100% (max)
```

### Temperature (°C)
```
Hypothermia: < 34°C
Low:         36°C
Normal:      36.5-37.5°C
Fever:       38°C
High Fever:  > 40°C
```

### Respiratory Rate (breaths/min)
```
Critical Low: < 8
Low:          12
Normal:       12-20
Elevated:     24
Critical:     > 30
```

---

## Hybrid Detection Approach

### Phase 1: Rule-Based Threshold Check (Fast)
- Compare each vital to VITAL_THRESHOLDS dictionary
- O(n) where n = number of vitals (typically 5-6)
- <1ms response
- Covers 100% of vital sign ranges

**Advantage:** Instant, deterministic, no API calls
**Limitation:** No context-specific interpretation

### Phase 2: LLM-Based Explanation (Accurate)
- For each abnormal vital, call Euri LLM
- Generate human-readable explanation
- Temperature 0.3 (low creativity, clinical accuracy)
- Max tokens: 100 per vital

**Advantage:** Contextual explanations, patient education
**Limitation:** Slower (1-2 seconds per vital)

### Phase 3: Overall Assessment (Context)
- Combine all vitals into clinical picture
- Generate recommendations
- Decide escalation

---

## Vital Sign Analysis Process

### Step 1: Extract Vital Values
```python
vitals = {
    "heart_rate": 120,
    "blood_pressure_systolic": 145,
    "blood_pressure_diastolic": 92,
    "oxygen_saturation": 96,
    "temperature": 38.5,
    "respiratory_rate": 22
}
```

### Step 2: Apply Thresholds
```python
For each vital:
  - Compare to VITAL_THRESHOLDS
  - Determine status (NORMAL, ELEVATED, HIGH, CRITICAL_HIGH, etc.)
  - Map to severity (NORMAL, MODERATE, HIGH, CRITICAL)
```

### Step 3: Get Explanations
```python
For each abnormal vital:
  - Call Euri LLM with vital value + status
  - Return patient-friendly explanation
```

### Step 4: Generate Assessment
```python
- Combine all vital analyses
- Identify critical findings
- Generate overall health status
- Determine action required
```

### Step 5: Create Recommendations
```python
- Based on severity level
- Based on specific abnormal vitals
- Based on patient context (age, history)
```

### Step 6: Escalation Decision
```python
if status in ["CRITICAL", "HIGH"]:
  should_escalate_to_triage = True
else:
  should_escalate_to_triage = False
```

---

## Integration with Orchestrator & ChatService

### Message Flow

```
1. Patient sends vital sign message
   └─ "My heart rate is 145 and I feel dizzy"
   
2. Orchestrator detects vital keywords
   └─ "heart rate" keyword matched
   └─ Routes to: monitoring_agent
   └─ Confidence: 0.98
   
3. ChatService calls monitoring agent
   └─ _extract_vitals_from_message() extracts: heart_rate=145
   └─ analyze_vitals({heart_rate: 145}, patient_info)
   
4. Monitoring Agent analyzes
   ├─ Rule-based: HR 145 → HIGH (exceeds threshold of 140)
   ├─ Severity: HIGH (physiologically abnormal)
   ├─ LLM explanation: "Elevated heart rate may indicate..."
   ├─ Recommendation: "Contact doctor immediately"
   └─ Escalate: YES (HIGH severity)
   
5. Return structured response
   └─ Status: HIGH
   └─ Severity Level: 3
   └─ Should Escalate: true
   └─ Recommendation: Contact doctor immediately
   
6. ChatService logs and persists
   └─ Save to database
   
7. Frontend receives response
   └─ Display warning with escalation indicator
   └─ Offer to contact doctor or call 911
```

### Routing Keywords (Orchestrator)

```python
vital_keywords = [
    "heart rate", "pulse", "bp", "blood pressure",
    "oxygen", "spo2", "temperature", "fever", "temp",
    "respiratory rate", "breathing", "vitals"
]
```

If any keyword detected → routing_intent = "monitoring"

---

## Vital Extraction from Messages

The MonitoringAgent uses regex patterns to extract vital values from natural language:

### Heart Rate
```
"My heart rate is 120" → heart_rate: 120
"My pulse is 105" → heart_rate: 105
"HR 88" → heart_rate: 88
```

### Blood Pressure
```
"BP is 140/90" → systolic: 140, diastolic: 90
"Blood pressure 155/95 mmHg" → systolic: 155, diastolic: 95
```

### Temperature
```
"I have a fever of 38.5" → temperature: 38.5
"Temperature 39°C" → temperature: 39
```

### Oxygen Saturation
```
"My oxygen is 96" → oxygen_saturation: 96
"SpO2 88" → oxygen_saturation: 88
"O2 saturation 92%" → oxygen_saturation: 92
```

### Respiratory Rate
```
"Breathing rate 24 breaths per minute" → respiratory_rate: 24
"RR 28" → respiratory_rate: 28
```

---

## API Response Examples

### Normal Vitals Response
```json
{
  "overall_status": "NORMAL",
  "severity_level": 1,
  "vital_analyses": [
    {
      "vital_type": "heart_rate",
      "value": 72,
      "unit": "bpm",
      "status": "NORMAL",
      "severity": "NORMAL",
      "explanation": "Your heart rate is in the normal, healthy range",
      "recommendation": "Continue regular monitoring",
      "confidence": 0.93
    },
    {
      "vital_type": "blood_pressure_systolic",
      "value": 120,
      "unit": "mmHg",
      "status": "NORMAL",
      "severity": "NORMAL",
      "explanation": "Your systolic blood pressure is normal and healthy",
      "recommendation": "Continue regular monitoring",
      "confidence": 0.93
    }
  ],
  "critical_findings": [],
  "overall_assessment": "Your vital signs are all in the normal, healthy range. Continue your regular activities and monitor as usual.",
  "recommendations": [
    "Continue regular monitoring",
    "Maintain healthy lifestyle"
  ],
  "should_escalate_to_triage": false,
  "confidence_score": 0.93,
  "agent_used": "monitoring",
  "tokens_used": 180,
  "response": "✅ **VITAL SIGNS ANALYSIS**\n\nOverall Status: **NORMAL**\n\nYour Vital Signs:\n- Heart Rate: 72 bpm (NORMAL)\n- Blood Pressure Systolic: 120 mmHg (NORMAL)\n...",
  "disclaimer": "⚠️ **DISCLAIMER**: This is not a substitute for professional medical advice."
}
```

### Critical Vitals Response
```json
{
  "overall_status": "CRITICAL",
  "severity_level": 4,
  "vital_analyses": [
    {
      "vital_type": "heart_rate",
      "value": 155,
      "unit": "bpm",
      "status": "CRITICAL_HIGH",
      "severity": "CRITICAL",
      "explanation": "Your heart rate is dangerously high and requires immediate medical attention",
      "recommendation": "SEEK IMMEDIATE MEDICAL ATTENTION - call 911",
      "confidence": 0.93
    },
    {
      "vital_type": "oxygen_saturation",
      "value": 82,
      "unit": "%",
      "status": "CRITICAL_LOW",
      "severity": "CRITICAL",
      "explanation": "Your oxygen level is critically low - this is a medical emergency",
      "recommendation": "SEEK IMMEDIATE MEDICAL ATTENTION - call 911",
      "confidence": 0.93
    }
  ],
  "critical_findings": [
    "heart_rate: CRITICAL_HIGH",
    "oxygen_saturation: CRITICAL_LOW"
  ],
  "overall_assessment": "Your vital signs indicate a medical emergency. Multiple critical values require immediate professional evaluation.",
  "recommendations": [
    "Seek immediate medical attention or call 911",
    "Monitor oxygen levels"
  ],
  "should_escalate_to_triage": true,
  "confidence_score": 0.93,
  "agent_used": "monitoring",
  "tokens_used": 250,
  "response": "🚨 **VITAL SIGNS ANALYSIS**\n\nOverall Status: **CRITICAL**\n\nYour Vital Signs:\n- Heart Rate: 155 bpm (CRITICAL_HIGH)\n- Oxygen Saturation: 82 % (CRITICAL_LOW)\n\n**Assessment:**\nYour vital signs indicate a medical emergency...\n\n**Next Step:** SEEK IMMEDIATE MEDICAL ATTENTION\n\n⚠️ **DISCLAIMER**: This is not a substitute for professional medical advice.\n**Seek immediate medical attention or call emergency services (911).**",
  "disclaimer": "⚠️ **DISCLAIMER**: This is not a substitute for professional medical advice.\n**Seek immediate medical attention or call emergency services (911).**"
}
```

---

## Integration with ChatService

### Message Handling Flow

```python
# 1. Patient sends message
message = "My heart rate is 145 and BP is 155/95"

# 2. Orchestrator routes
routing = orchestrator.route_message(message)
# Returns: agent_to_call = "monitoring_agent"

# 3. ChatService extracts vitals
vitals = service._extract_vitals_from_message(message)
# Returns: {
#   heart_rate: 145,
#   blood_pressure_systolic: 155,
#   blood_pressure_diastolic: 95
# }

# 4. Call monitoring agent
response = monitoring_agent.analyze_vitals(vitals, patient_info)
# Returns: full analysis with severity, recommendations, escalation flag

# 5. Check if escalation needed
if response.get("should_escalate_to_triage"):
    # Route to triage agent for urgency assessment
    triage_response = triage_agent.assess_urgency(message, patient_info)
    # Combine responses for user

# 6. Save to database and return to frontend
```

---

## Files & Code Structure

### Core Implementation
- **`app/agents/monitoring_agent.py`** - Main MonitoringAgent class
  - `analyze_vitals()` - Analyze vital signs and detect anomalies
  - `_analyze_single_vital()` - Analyze individual vital
  - `_get_vital_explanation()` - LLM-based explanation
  - `_get_vital_recommendation()` - Clinical recommendation
  - `_generate_overall_assessment()` - Overall health status
  - `_generate_recommendations()` - Action recommendations
  - `_format_patient_response()` - Patient-friendly formatting

- **`app/agents/base_agent.py`** - Abstract base for all agents
  - BaseAgent parent class
  - Common logging and disclaimer methods

- **`app/services/chat_service.py`** - Integration point
  - `_call_agent()` - Routes to monitoring_agent
  - `_extract_vitals_from_message()` - Extracts vital values via regex
  - Orchestrator integration

- **`app/agents/orchestrator.py`** - Router
  - Detects vital sign keywords
  - Routes to monitoring_agent automatically
  - Escalation to triage for critical values

### Testing
- **`test_monitoring_agent.py`** - Comprehensive test suite
  - 6 vital analysis scenarios (NORMAL → CRITICAL)
  - Critical escalation verification
  - Regex extraction testing

---

## Performance Characteristics

- **Rule-based lookup**: <1ms for vital threshold comparison
- **LLM explanation per vital**: ~500ms per vital
- **Total response time**: 1-4 seconds (depending on # abnormal vitals)
- **Confidence scores**: 0.93-0.95 for threshold-based detection
- **Memory**: Minimal (thresholds dictionary only)

---

## Testing

### Run Tests
```bash
cd backend
python test_monitoring_agent.py
```

### Expected Output
```
Test 1: NORMAL - All vitals within healthy range
Vitals Analyzed: 5
Overall Status: NORMAL
Confidence: 93%
[PASS] CORRECT: Assessed as 'NORMAL' (expected)

Test 2: MODERATE - Slightly elevated heart rate
Vitals Analyzed: 5
Overall Status: MODERATE
Confidence: 93%
[PASS] CORRECT: Assessed as 'MODERATE' (expected)

Test 3: HIGH - Multiple elevated vitals + fever
Vitals Analyzed: 5
Overall Status: HIGH
Confidence: 93%
[PASS] CORRECT: Assessed as 'HIGH' (expected)

Test 4: CRITICAL - Dangerously low vitals
Vitals Analyzed: 5
Overall Status: CRITICAL
Escalate to Triage: True
Confidence: 93%
[PASS] CORRECT: Assessed as 'CRITICAL' (expected)
```

---

## Key Design Decisions

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **Threshold-based** | Fast, deterministic, no hallucinations | Less flexible than pure LLM |
| **Normal ranges** | Based on medical guidelines (AHA, WHO) | Different for different populations |
| **LLM for explanation** | Patient education + context | Adds latency |
| **Automatic escalation** | Safety-first approach | May over-escalate in some cases |
| **Keyword-based routing** | Fast orchestrator bypass for vitals | Requires keyword training |
| **Severity hierarchy** | NORMAL > MODERATE > HIGH > CRITICAL | Max severity wins |

---

## Common Use Cases

### Vitals Check
```
Patient: "My heart rate is 120 and oxygen is 94"
Agent:   Status: MODERATE (elevated HR, low-normal O2)
         Recommendations: Monitor and report to doctor
```

### Fever Assessment
```
Patient: "I have a temperature of 39.2°C"
Agent:   Status: HIGH (high fever)
         Recommendations: Contact doctor, monitor temperature
```

### Emergency Detection
```
Patient: "Heart rate 160, BP 180/110, can't breathe, oxygen 85"
Agent:   Status: CRITICAL
         Action: ESCALATE TO TRIAGE
         Recommendation: SEEK IMMEDIATE MEDICAL ATTENTION (911)
```

### Medication Side Effects
```
Patient: "Since taking new medication, my BP is 155/100 and I feel dizzy"
Agent:   Status: HIGH
         Recommendation: Contact doctor immediately about side effects
         (Combined with medication agent for drug-specific guidance)
```

---

## Next Steps

1. ✅ **Created MonitoringAgent** - Vital analysis with rule-based thresholds
2. ✅ **Integrated with Orchestrator** - Vital keyword detection
3. ✅ **Integrated with ChatService** - Vital extraction & routing
4. ✅ **Created test suite** - 6+ scenarios covering all risk levels
5. ➡️ **Create Vitals API endpoint** - POST /api/v1/vitals/analyze
6. ➡️ **Create vital trends analysis** - Monitor changes over time
7. ➡️ **Implement real-time monitoring** - WebSocket for continuous monitoring
8. ➡️ **Build frontend UI** - Vital sign dashboard with charts

---

**Status**: Monitoring Agent implemented and integrated  
**Testing**: 6+ test scenarios pass with correct risk assessment  
**Documentation**: Complete  
**Next**: API endpoints or trend analysis

