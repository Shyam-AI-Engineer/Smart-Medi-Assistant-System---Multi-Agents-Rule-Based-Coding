# Euri API + FAISS Architecture

> Unified AI provider (Euri) + local vector database (FAISS) for medical RAG system

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                              │
│              (Patient Chat, Doctor Dashboard)                     │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP/JSON
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                                │
│              (Routes, Services, Agents)                           │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                          │
               ▼ (embedding API)          ▼ (LLM API)
        ┌─────────────────────────────────────────┐
        │  EURI API (OpenAI-Compatible)           │
        │  https://api.euron.one/api/v1/euri      │
        │                                         │
        │  - Model: gemini-embedding-2-preview    │
        │    (768 dimensions)                     │
        │                                         │
        │  - Model: gpt-4o-mini                   │
        │    (Medical responses)                  │
        │                                         │
        │  Single API Key: EURI_API_KEY           │
        └─────────────────────────────────────────┘
               │
               │ (stores vectors + metadata)
               ▼
        ┌─────────────────────────┐
        │  FAISS Index (Local)     │
        │  /data/faiss_index/      │
        │                          │
        │ - faiss_index.bin (768d) │
        │ - faiss_metadata.json    │
        │                          │
        │ Max: 1M+ documents       │
        │ No cloud cost            │
        └─────────────────────────┘
               │
               │ (search results)
               ▼
        ┌──────────────────────────┐
        │  LLM Prompt Assembly      │
        │  (RAG Context)            │
        └──────────────────────────┘
               │
               │ (context + question)
               ▼
        ┌──────────────────────────┐
        │  Euri LLM Generation      │
        │  (gpt-4o-mini)           │
        │  temp=0.3 (factual)      │
        └──────────────────────────┘
               │
               │ (response)
               ▼
        ┌──────────────────────────┐
        │  Response to Frontend     │
        │  + Source References     │
        └──────────────────────────┘
```

---

## Data Flow: Medical Question to Answer

```
1. FRONTEND (Next.js)
   Patient types: "I have chest pain and shortness of breath"
   └─ Sends POST /api/v1/chat

2. BACKEND ROUTE (FastAPI)
   - Validates JWT token
   - Validates input (Pydantic)
   - Gets current user from token
   └─ Calls ChatService

3. CHAT SERVICE (orchestration)
   - Routes to appropriate agent (Orchestrator → Clinical)
   └─ Calls ClinicalAgent

4. CLINICAL AGENT (business logic)
   - Question: "I have chest pain..."
   
   a) EMBEDDING STEP (Euri)
      └─ euri.embed_text(question)
      └─ Returns: [0.45, -0.12, 0.89, ...] (768 floats)
   
   b) SEARCH STEP (FAISS)
      └─ faiss.search_medical_context(embedding, top_k=5)
      └─ Returns: [
           {"source_file": "cardiology_guidelines.pdf", "score": 0.94, ...},
           {"source_file": "chest_pain_diagnosis.txt", "score": 0.91, ...},
           ...
         ]
   
   c) CONTEXT ASSEMBLY
      └─ Format retrieved documents for LLM:
         "Retrieved Medical Information:
          Document 1: cardiology_guidelines.pdf
          Relevance: 94%
          Content: Treatment for chest pain includes...
          
          Document 2: chest_pain_diagnosis.txt
          Relevance: 91%
          Content: Differential diagnosis..."
   
   d) GENERATION STEP (Euri LLM)
      └─ euri.generate_medical_response(
            question="I have chest pain and shortness of breath",
            context="Retrieved Medical Information: ...",
            patient_info={"age": 45, "allergies": ["Aspirin"], ...}
         )
      └─ Returns: "Based on medical guidelines, chest pain with 
                   shortness of breath may indicate several conditions...
                   IMPORTANT DISCLAIMER: Seek immediate medical attention
                   if you experience severe chest pain..."

5. AGENT RETURNS
   {
     "response": "Based on medical guidelines...",
     "sources": [
       {"file": "cardiology_guidelines.pdf", "relevance": "94%", ...},
       {"file": "chest_pain_diagnosis.txt", "relevance": "91%", ...}
     ],
     "confidence_score": 0.92,
     "agent_used": "clinical",
     "tokens_used": 1240
   }

6. BACKEND SERVICE → Route → Response
   └─ HTTP 200 with JSON response

7. FRONTEND (Next.js)
   └─ Displays answer + source cards
   └─ User can click sources to see full context
```

---

## Service Layer Architecture

### Three-Tier Service Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    API Routes                               │
│              (app/api/v1/*.py)                              │
│  - Input validation (Pydantic)                              │
│  - JWT token validation                                     │
│  - HTTP response formatting                                │
│  - NO business logic here                                   │
└──────────────────┬──────────────────────────────────────────┘
                   │ Depends on (FastAPI Depends)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│             Application Services                            │
│         (app/services/*.py)                                 │
│  - ChatService (orchestrates chat)                          │
│  - PatientService (patient CRUD)                            │
│  - Calls agents & data access                               │
│  - Error handling & retry logic                             │
│  - Caching decisions                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │ Uses
                   ├─────────────────────┬──────────────────┐
                   ▼                     ▼                  ▼
        ┌────────────────────┐ ┌────────────────┐ ┌──────────────┐
        │ EuriService        │ │ FAISSService   │ │ ChatService  │
        │ (AI API wrapper)   │ │ (Vector DB)    │ │ (Orchestrate)│
        │                    │ │                │ │              │
        │ - embed_text()     │ │ - search()     │ │ - handle()   │
        │ - generate_*()     │ │ - add_doc()    │ │ - retrieve() │
        │ - health_check()   │ │ - delete_doc() │ │              │
        └────────────────────┘ └────────────────┘ └──────────────┘
                   │                     │
                   ▼                     ▼
        ┌────────────────────┐ ┌──────────────────┐
        │ Euri API           │ │ FAISS Local DB   │
        │ (External Cloud)   │ │ (./data/...)     │
        │                    │ │                  │
        │ - HTTP/REST        │ │ - Binary index   │
        │ - OpenAI SDK       │ │ - JSON metadata  │
        └────────────────────┘ └──────────────────┘
```

### Dependency Injection (FastAPI Depends Pattern)

```python
# In routes (app/api/v1/chat.py)
@router.post("/api/v1/chat")
def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),  # JWT validation
    db: Session = Depends(get_db),                    # Database
):
    service = ChatService(db)  # Inject services
    response = service.handle_message(request, current_user)
    return response

# ChatService uses dependencies internally
class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.euri = get_euri_service()      # Singleton
        self.faiss = get_faiss_service()    # Singleton
        self.agent = get_clinical_agent()   # Or route to others

    def handle_message(self, message: str, user_id: str):
        # 1. Get agent
        intent = self.euri.generate_orchestrator_response(message)
        
        # 2. Route to agent
        if intent["agent_to_call"] == "clinical":
            agent_response = self.agent.answer_medical_question(message)
        
        # 3. Save to database
        chat = ChatHistory(
            user_message=message,
            ai_response=agent_response["response"],
            agent_used=agent_response["agent_used"],
            confidence_score=agent_response["confidence_score"],
            tokens_used=agent_response["tokens_used"],
        )
        self.db.add(chat)
        self.db.commit()
        
        return agent_response
```

---

## Agent Routing

### Orchestrator Agent (GPT-4o-mini via Euri)

Analyzes patient message and routes to specialist:

```
Patient: "Can I take ibuprofen with my current medications?"
           │
           ▼
Orchestrator (Euri LLM):
- Intent: "medication_interaction"
- Confidence: 0.98
- Route to: medication_agent
           │
           ▼
Medication Agent (via clinical_agent.py for now):
- Checks knowledge base for drug interactions
- Returns: "Your medications may interact with..."
```

### Available Agents

| Agent | Purpose | Data Source | LLM |
|-------|---------|-------------|-----|
| **Clinical** | Medical knowledge, symptoms | FAISS (medical docs) | Euri |
| **RAG** | Document retrieval | FAISS | Euri |
| **Medication** | Drug interactions | FAISS (formulary) | Euri |
| **Triage** | Urgency assessment | FAISS (protocols) | Euri |
| **Monitoring** | Vital sign trends | Database (vitals) | Euri |

All agents use the same **Euri API** for embeddings and generation.

---

## Error Handling & Graceful Degradation

### Euri API Failure

```python
try:
    embedding = euri.embed_text(content)
except APIError as e:
    logger.error(f"Euri API failed: {e}")
    # Fallback: return cached response or basic answer
    return {
        "response": "I'm temporarily unable to process your question. Please try again.",
        "error": "AI service unavailable",
        "fallback": True
    }
```

### FAISS Search Failure

```python
try:
    context = faiss.retrieve_medical_context(embedding)
except Exception as e:
    logger.error(f"FAISS search failed: {e}")
    # Fallback: generate response WITHOUT context (lower quality)
    response = euri.generate_medical_response(
        question,
        medical_context="No medical documents available. Providing general information only.",
        patient_info=None
    )
    return response
```

### Both Services Down

```python
if not euri.health_check() or not faiss.health_check():
    return {
        "response": "Medical AI services are temporarily unavailable. Please contact support.",
        "status": "service_degraded"
    }
```

---

## Environment Configuration

### `.env` File

```bash
# Euri API
EURI_API_KEY=sk-proj-xxxxxxxxxxxxx
EURI_BASE_URL=https://api.euron.one/api/v1/euri
EURI_EMBEDDING_MODEL=gemini-embedding-2-preview
EURI_LLM_MODEL=gpt-4o-mini

# FAISS Local
FAISS_INDEX_PATH=./data/faiss_index
EMBEDDING_DIMENSIONS=768
CHUNK_SIZE=1024
CHUNK_OVERLAP=256

# RAG Settings
RAG_TOP_K=5
TEMPERATURE_RAG=0.3
```

---

## Performance Characteristics

### Embedding (Euri)
- Model: `gemini-embedding-2-preview`
- Dimensions: 768
- Speed: ~100ms per request
- Cost: Billed per 1K input tokens
- Max input: 8192 tokens per request

### Search (FAISS)
- Algorithm: Flat L2 (Euclidean distance)
- Speed: <1ms for 1M vectors
- Memory: ~768 floats × doc_count × 4 bytes
- Example: 100k docs ≈ 300MB RAM

### Generation (Euri)
- Model: `gpt-4o-mini`
- Temperature: 0.3 (factual, low creativity)
- Max tokens: 2048 default
- Speed: ~2-5 seconds including streaming

---

## Development Workflow

### 1. Start Backend

```bash
cd backend
source venv/Scripts/activate
uvicorn app.main:app --reload
```

### 2. Test FAISS + Euri Integration

```bash
# Add a medical document to knowledge base
python -c "
from app.services.euri_service import get_euri_service
from app.services.faiss_service import get_faiss_service
from app.agents.clinical_agent import get_clinical_agent

agent = get_clinical_agent()
result = agent.ingest_medical_document(
    content='Chest pain may indicate...',
    source_type='text',
    source_name='symptom_guide.txt'
)
print(f'Document added: {result}')
"

# Ask a question
python -c "
from app.agents.clinical_agent import get_clinical_agent

agent = get_clinical_agent()
result = agent.answer_medical_question('What causes chest pain?')
print(f'Response: {result[\"response\"]}')
print(f'Sources: {result[\"sources\"]}')
"
```

### 3. Monitor Services

```bash
# Check if services are healthy
curl http://localhost:8000/health
# Returns: {"euri": true/false, "faiss": true/false}
```

---

## Key Reminders

- **Euri is OpenAI-compatible** — use OpenAI SDK with custom base_url
- **Single API key** — `EURI_API_KEY` for both embeddings and LLM
- **FAISS is local** — no cloud costs, but limited to single machine
- **768 dimensions** — Gemini Embedding 2 output size (immutable)
- **RAG-first approach** — always retrieve context before generating medical responses
- **No hallucinations** — Euri is instructed to say "insufficient context" rather than guess
- **Medical disclaimers** — always included in patient-facing responses

---

## Next Steps

1. ✅ Created EuriService (embeddings + LLM)
2. ✅ Created FAISSService (vector storage)
3. ✅ Created ClinicalAgent (RAG + medical Q&A)
4. ➡️ Create ChatService (orchestrator)
5. ➡️ Create API routes (chat, ingest, health)
6. ➡️ Test end-to-end with sample medical documents
7. ➡️ Build frontend chat UI
