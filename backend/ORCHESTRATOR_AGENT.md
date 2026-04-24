# Orchestrator Agent - Message Routing System

The Orchestrator Agent analyzes patient messages and routes them to the appropriate specialist agent.

## Architecture

```
Patient Message
    │
    ▼
┌─────────────────────────────┐
│   Orchestrator Agent        │
│                             │
│ 1. Check critical symptoms  │
│    (chest pain, etc.)       │
│    └─ If YES → Triage agent │
│                             │
│ 2. Analyze intent           │
│    (via Euri LLM)           │
│    └─ Classify into:        │
│       - Clinical            │
│       - Medication          │
│       - RAG                 │
│       - Monitoring          │
│       - Triage              │
└──────────────┬──────────────┘
               │
    ┌──────────┴────────┬────────┬──────────┐
    ▼                   ▼        ▼          ▼
┌──────────┐     ┌────────────┐ ┌──────┐ ┌──────────┐
│ Clinical │     │ Medication │ │ Triage│ │ RAG/etc  │
│  Agent   │     │   Agent    │ │Agent │ │  Agent   │
└──────────┘     └────────────┘ └──────┘ └──────────┘
    │                   │        │          │
    └──────────────────┴────────┴──────────┘
                      │
                      ▼
            Return AI Response
```

## Agent Routing

| Agent | Trigger | Example |
|-------|---------|---------|
| **Triage** | Critical symptoms detected | "Chest pain", "Can't breathe", "Severe bleeding" |
| **Clinical** | Symptom analysis, medical knowledge | "I have a headache and fever", "What causes migraines?" |
| **Medication** | Drug interactions, contraindications | "Can I take ibuprofen with blood pressure meds?" |
| **RAG** | Medical document/literature retrieval | "Tell me about diabetes treatment guidelines" |
| **Monitoring** | Vital sign trends, anomaly detection | "My heart rate is 120 bpm" |

## Files

### Core Implementation
- **`app/agents/orchestrator.py`** - Main OrchestratorAgent class
  - `route_message()` - Analyzes intent and routes
  - `should_escalate_to_triage()` - Detects critical symptoms
  - `get_routing_explanation()` - Human-readable explanation

- **`app/services/chat_service.py`** - Enhanced to use Orchestrator
  - Initializes OrchestratorAgent
  - Checks for critical symptoms
  - Routes to specialist agents

### Dependencies
- **`app/services/euri_service.py`** - Provides LLM for intent analysis
  - `generate_orchestrator_response()` - Euri call for routing

## How It Works

### Step 1: Critical Symptom Detection
```python
orchestrator.should_escalate_to_triage(message)
```

Checks for keywords like:
- "chest pain", "difficulty breathing", "loss of consciousness"
- "severe bleeding", "choking", "seizure"
- If found → **Always** route to Triage agent

### Step 2: Intent Analysis (Euri LLM)
If not critical, analyze with Euri:

```python
routing = orchestrator.route_message(patient_message)
```

Euri LLM receives:
```
"You are the orchestrator agent for a medical AI assistant.
Your job is to analyze patient messages and route them to the correct specialist agent.

Available agents:
- clinical: Medical knowledge, symptom analysis, differential diagnosis
- rag: Medical document/literature retrieval and analysis
- medication: Drug interactions, contraindications, warnings
- triage: Urgency assessment, emergency detection

Respond with ONLY valid JSON:
{
    "routing_intent": "clinical|rag|medication|triage",
    "confidence": 0.0-1.0,
    "reason": "Why you chose this routing",
    "agent_to_call": "agent_name"
}"
```

### Step 3: Response
```json
{
  "routing_intent": "clinical",
  "confidence": 0.95,
  "reason": "User asked about symptom analysis",
  "agent_to_call": "clinical_agent"
}
```

### Step 4: Agent Dispatch (ChatService)
```python
# In ChatService._call_agent()
if agent_name == "clinical_agent":
    response = self.clinical_agent.answer_medical_question(message)
elif agent_name == "medication_agent":
    response = self.medication_agent.check_interactions(message)
elif agent_name == "triage_agent":
    response = self.triage_agent.assess_urgency(message)
# ... etc
```

## Testing

### Run the test script
```bash
cd backend
python test_orchestrator.py
```

This tests routing on 5 different medical scenarios:
1. Critical symptom (chest pain)
2. Drug interaction question
3. Symptom analysis
4. Document retrieval
5. Vital sign analysis

### Expected Output
```
Test 1: Critical symptom - should detect urgency
Message: "I have a severe chest pain and difficulty breathing"
✅ CRITICAL: Escalated to triage

Test 2: Drug interaction question
Message: "Can I take ibuprofen with my blood pressure medication?"
Agent: MEDICATION
Confidence: 95%
Reason: User asked about potential drug interactions
✅ CORRECT: Matched expected intent 'medication'

...
```

## Integration with Chat Endpoint

The Chat endpoint now uses the Orchestrator:

```python
# POST /api/v1/chat
{
  "message": "I have chest pain and shortness of breath"
}

# Processing flow:
1. ChatService.handle_message() is called
2. orchestrator.should_escalate_to_triage() checks for keywords
3. Detects "chest pain" → routes to "triage_agent"
4. Triage agent returns urgent medical advice
5. Response saved to database
6. Returned to frontend

# Response:
{
  "response": "URGENT: Seek immediate medical attention...",
  "agent_used": "triage_agent",
  "confidence_score": 0.99,
  "sources": [...],
  ...
}
```

## Next Steps

1. ✅ **Orchestrator Agent created** - Routes messages to specialists
2. ➡️ **Implement Triage Agent** - Urgency assessment
3. ➡️ **Implement Medication Agent** - Drug interactions
4. ➡️ **Implement Monitoring Agent** - Vital sign analysis
5. ➡️ **Test end-to-end routing** - Send messages to chat endpoint

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Critical symptom detection first** | Safety - don't wait for LLM if life-threatening |
| **Euri for intent analysis** | Accurate classification with full context |
| **Fallback to clinical** | If routing fails, clinical is safest default |
| **High confidence on critical** | 0.99 confidence to ensure triage takes priority |
| **Structured JSON response** | Deterministic routing, easy to parse and log |

## Logging & Debugging

Enable debug output:
```bash
# Backend logs show:
DEBUG [ORCHESTRATOR]: Analyzing message: Can I take ibuprofen...
DEBUG [ORCHESTRATOR]: Routed to medication_agent (confidence: 0.95)

# Structured logs:
chat.message.routed agent=medication_agent confidence=0.95
```

## API Response with Routing

```json
{
  "response": "Ibuprofen and blood pressure medications...",
  "sources": [...],
  "agent_used": "medication_agent",
  "confidence_score": 0.95,
  "tokens_used": 450,
  "error": false
}
```

The `agent_used` field shows which agent handled the message.
