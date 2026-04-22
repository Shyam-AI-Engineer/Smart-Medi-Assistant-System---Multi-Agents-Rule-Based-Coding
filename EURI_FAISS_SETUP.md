# Euri API + FAISS Integration - Setup Complete ✅

## What We've Built

A **production-ready medical AI system** with:
- **Euri API** - unified embeddings + LLM via OpenAI SDK
- **FAISS** - local vector database (768-dimensional)
- **RAG Pipeline** - question → embed → search → retrieve → generate → answer
- **Error Handling** - graceful degradation, retries, fallbacks
- **Clean Architecture** - service layer pattern, no business logic in routes

---

## Files Created

### 1. Configuration & Environment

```
backend/.env.example          ← Template (commit to git)
backend/.env                  ← Local secrets (in .gitignore)
backend/app/services/euri_service.py    ← Euri client (embeddings + LLM)
backend/app/services/faiss_service.py   ← FAISS vector DB client
```

### 2. Agent Integration

```
backend/app/agents/clinical_agent.py    ← Example: Medical Q&A with RAG
```

### 3. Architecture & Guidelines

```
.claude/rules/06-euri-faiss-architecture.md   ← System design + data flow
.claude/rules/07-euri-error-handling.md       ← Error handling patterns
```

---

## Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
cd backend

# Add to requirements.txt:
openai>=1.68.0
faiss-cpu>=1.7.0
numpy>=1.24.0
tenacity>=9.0.0

pip install -r requirements.txt
```

### Step 2: Configure .env

```bash
# Copy and fill in your actual keys
cp .env.example .env

# Edit .env and set:
EURI_API_KEY=sk-proj-your-actual-key-here
```

### Step 3: Test Services

```bash
python -c "
from app.services.euri_service import get_euri_service
from app.services.faiss_service import get_faiss_service

euri = get_euri_service()
faiss = get_faiss_service()

print('✅ Euri:', euri.health_check())
print('✅ FAISS:', faiss.health_check())
"
```

### Step 4: Add a Medical Document to Knowledge Base

```bash
python -c "
from app.agents.clinical_agent import get_clinical_agent

agent = get_clinical_agent()

# Add a medical document
result = agent.ingest_medical_document(
    content='Chest pain may indicate heart disease, anxiety, or muscle strain. Seek immediate care if severe.',
    source_type='text',
    source_name='chest_pain_guide.txt'
)

print(f'✅ Document added: {result}')
"
```

### Step 5: Ask a Question (RAG in Action)

```bash
python -c "
from app.agents.clinical_agent import get_clinical_agent

agent = get_clinical_agent()

# Ask a question - will search FAISS + use Euri to answer
result = agent.answer_medical_question('What causes chest pain?')

print('Response:', result['response'])
print('Sources:', result['sources'])
print('Confidence:', result['confidence_score'])
"
```

---

## Architecture Overview

```
Patient Question
    ↓
[FastAPI Route] - validates JWT, checks input
    ↓
[ChatService] - orchestrates services
    ↓
[ClinicalAgent] - business logic
    ├─ [EuriService] - embed question (768 dims)
    ├─ [FAISSService] - search knowledge base (top 5 results)
    └─ [EuriService] - generate response with context
    ↓
[Response + Sources + Confidence]
    ↓
[Frontend] - display to patient
```

---

## Core Services

### EuriService

```python
from app.services.euri_service import get_euri_service

euri = get_euri_service()

# Embed text (question, document, etc)
embedding = euri.embed_text("What is diabetes?")  # → 768 floats

# Embed medical content with metadata
result = euri.embed_medical_content(
    content="Diabetes is...",
    content_type="pdf",
    source_name="diabetes_guide.pdf"
)

# Generate medical response with RAG
response = euri.generate_medical_response(
    patient_question="I have high blood sugar",
    medical_context="Retrieved from FAISS: ...",
    patient_info={"age": 45, "allergies": ["Aspirin"]}
)

# Orchestrator routing
routing = euri.generate_orchestrator_response("Can I take ibuprofen?")
# → {"routing_intent": "medication", "agent_to_call": "medication_agent"}
```

### FAISSService

```python
from app.services.faiss_service import get_faiss_service

faiss = get_faiss_service()

# Add document to knowledge base
doc_id = faiss.add_medical_document(
    embedding=[0.45, -0.12, ...],  # 768 dims
    source_type="pdf",
    source_file="guidelines.pdf",
    content_preview="Treatment involves..."
)

# Search for relevant documents
matches = faiss.search_medical_context(
    query_embedding=[0.42, -0.10, ...],
    top_k=5  # Return top 5 most relevant
)

# Retrieve formatted context for RAG
context = faiss.retrieve_medical_context(
    query_embedding=[...],
    patient_id="patient_123"
)

# List all documents
docs = faiss.list_documents(source_type="pdf")
```

### ClinicalAgent

```python
from app.agents.clinical_agent import get_clinical_agent

agent = get_clinical_agent()

# Answer medical question with RAG
response = agent.answer_medical_question(
    patient_question="I have chest pain",
    patient_info={"age": 45, "allergies": ["Aspirin"]}
)
# → {"response": "...", "sources": [...], "confidence": 0.92}

# Analyze symptoms
analysis = agent.analyze_symptoms(
    symptoms="Headache, fever, body aches",
    duration="3 days",
    patient_info={...}
)

# Ingest medical document
result = agent.ingest_medical_document(
    content="Medical guidelines...",
    source_type="pdf",
    source_name="clinical_guidelines.pdf"
)

# Get knowledge base stats
stats = agent.get_knowledge_base_stats()
# → {"total_documents": 42, "document_types": ["text", "pdf"]}
```

---

## Environment Variables

```bash
# Euri API
EURI_API_KEY=sk-proj-your-key          # Get from Euri
EURI_BASE_URL=https://api.euron.one/api/v1/euri
EURI_EMBEDDING_MODEL=gemini-embedding-2-preview
EURI_LLM_MODEL=gpt-4o-mini

# FAISS Local Vector DB
FAISS_INDEX_PATH=./data/faiss_index    # Local directory
EMBEDDING_DIMENSIONS=768               # Immutable

# RAG Configuration
RAG_TOP_K=5                            # Search top 5 documents
TEMPERATURE_RAG=0.3                    # Low creativity (factual)
CHUNK_SIZE=1024                        # For future document chunking
CHUNK_OVERLAP=256

# Other
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-min-32-chars
```

---

## Error Handling

### Automatic Retries

EuriService automatically retries on:
- Rate limit (429) - exponential backoff
- Connection errors - network issues
- Timeout errors - slow responses

Does NOT retry on:
- Authentication errors - API key invalid
- Validation errors - input too long

### Graceful Degradation

If Euri fails:
```
Full RAG (context + LLM) 
  → Falls back to: LLM without context (lower quality)
  → Falls back to: Cached response
  → Falls back to: Error message
```

If FAISS fails:
```
Search with filters
  → Falls back to: Basic search
  → Falls back to: Empty results (no context)
  → Service continues (uses LLM alone)
```

### Health Checks

```python
# Check all services
from app.services.euri_service import get_euri_service
from app.services.faiss_service import get_faiss_service

euri = get_euri_service()
faiss = get_faiss_service()

euri_status = euri.health_check()  # Dict with details
faiss_status = faiss.health_check()  # Boolean
```

---

## Data Flow Example: Patient Question

```
1. Patient types: "I have chest pain"
   └─ Frontend sends POST /api/v1/chat

2. Route receives request
   - Validates JWT token
   - Validates input (Pydantic)
   └─ Calls ChatService.handle_message()

3. ChatService
   - Gets patient from database
   └─ Calls ClinicalAgent.answer_medical_question()

4. ClinicalAgent
   
   a) Embedding (Euri)
      "I have chest pain"
      └─ [0.45, -0.12, 0.89, ... ] (768 floats)
   
   b) Search (FAISS)
      Search FAISS with embedding
      └─ Returns top 5 matches:
         - cardiology_guidelines.pdf (92% relevant)
         - chest_pain_diagnosis.txt (89%)
         - heart_disease_overview.pdf (87%)
         - anxiety_symptoms.pdf (72%)
         - muscle_strain_guide.pdf (68%)
   
   c) Context Assembly
      Format for LLM:
      "RETRIEVED MEDICAL INFORMATION:
       Document 1: cardiology_guidelines.pdf (92%)
       Treatment for chest pain includes...
       
       Document 2: chest_pain_diagnosis.txt (89%)
       Differential diagnosis..."
   
   d) Generation (Euri LLM)
      Question: "I have chest pain"
      Context: [formatted docs above]
      Patient info: age 45, allergies: ["Aspirin"]
      Temperature: 0.3 (factual)
      
      LLM generates:
      "Based on medical guidelines, chest pain may indicate:
       1. Heart disease - Seek immediate care if severe chest pressure
       2. Anxiety - May present as sharp pain with breathing difficulty
       3. Muscle strain - Improves with rest
       
       IMPORTANT: Seek immediate medical attention if experiencing...
       
       This is for informational purposes only."

5. Agent returns
   {
     "response": "Based on medical guidelines...",
     "sources": [
       {"file": "cardiology_guidelines.pdf", "relevance": "92%"},
       {"file": "chest_pain_diagnosis.txt", "relevance": "89%"}
     ],
     "confidence_score": 0.91,
     "agent_used": "clinical",
     "tokens_used": 1240
   }

6. ChatService saves to database
   db.add(ChatHistory(...))
   db.commit()

7. Route returns HTTP 200 with response

8. Frontend displays
   - Main response text
   - Source cards (click to see full context)
   - Confidence indicator
   - "Ask another question" input
```

---

## Next Steps (After This Setup)

### Phase 2: API Endpoints

Create FastAPI routes:
- `POST /api/v1/chat` - send message to medical AI
- `GET /api/v1/chat/history` - get conversation history
- `POST /api/v1/knowledge/ingest` - add medical documents
- `GET /api/v1/health` - system health check

### Phase 3: Frontend Chat UI

Build Next.js interface:
- Chat window with message bubbles
- Streaming responses (SSE)
- Source card display
- Document upload

### Phase 4: Additional Agents

Implement specialist agents:
- Medication Agent (drug interactions)
- Triage Agent (urgency assessment)
- RAG Agent (literature search)
- Monitoring Agent (vital analysis)

### Phase 5: Production Deployment

- Docker containerization
- Railway/Render backend hosting
- Vercel frontend hosting
- Production error monitoring (Sentry)

---

## Testing

### Unit Tests

```bash
cd backend
pytest tests/test_euri_service.py -v
pytest tests/test_faiss_service.py -v
pytest tests/test_clinical_agent.py -v
```

### Integration Tests

```bash
# Test full RAG pipeline
python -c "
from app.agents.clinical_agent import get_clinical_agent

agent = get_clinical_agent()

# Add doc
agent.ingest_medical_document(
    'Diabetes is a metabolic disorder...',
    'text',
    'diabetes.txt'
)

# Ask question
result = agent.answer_medical_question('What is diabetes?')
assert 'metabolic' in result['response'].lower()
assert len(result['sources']) > 0
print('✅ RAG pipeline works end-to-end')
"
```

---

## Troubleshooting

### "EURI_API_KEY not set"
```bash
# Check .env file
cat backend/.env | grep EURI_API_KEY

# If missing, add it:
echo "EURI_API_KEY=sk-proj-your-key" >> backend/.env
```

### "FAISS index is empty"
```bash
# This is normal on first run
# Add some documents:
python -c "
from app.agents.clinical_agent import get_clinical_agent
agent = get_clinical_agent()
agent.ingest_medical_document('Sample content...', 'text', 'sample.txt')
"
```

### "Euri health check failed"
```bash
# Check internet connection
ping api.euron.one

# Verify API key is valid
# Test with curl:
curl -X POST https://api.euron.one/api/v1/euri/embeddings \
  -H "Authorization: Bearer sk-proj-your-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"gemini-embedding-2-preview","input":"test"}'
```

---

## Key Reminders

✅ **Euri is OpenAI-compatible** - use OpenAI SDK with custom base_url
✅ **768 dimensions** - Gemini Embedding 2 output (immutable)
✅ **Single API key** - EURI_API_KEY for both embeddings and LLM
✅ **FAISS is local** - no cloud cost, but single-machine
✅ **RAG-first** - always retrieve context before generating medical responses
✅ **No hallucinations** - LLM instructed to say "insufficient context"
✅ **Graceful degradation** - services fail gracefully with fallbacks
✅ **Medical disclaimers** - always included in patient-facing responses

---

## Files & Locations

| File | Purpose |
|------|---------|
| `backend/.env` | Local secrets (git-ignored) |
| `backend/.env.example` | Template (committed) |
| `backend/app/services/euri_service.py` | Euri client |
| `backend/app/services/faiss_service.py` | FAISS client |
| `backend/app/agents/clinical_agent.py` | Medical Q&A agent |
| `.claude/rules/06-euri-faiss-architecture.md` | System design |
| `.claude/rules/07-euri-error-handling.md` | Error patterns |
| `backend/requirements.txt` | Python dependencies |
| `backend/app/models/chat_history.py` | Chat storage |
| `backend/app/models/__init__.py` | Model exports |

---

## Success Criteria

You'll know this is working when:

- ✅ `python -c "from app.services.euri_service import get_euri_service; print(get_euri_service().health_check())"` returns healthy status
- ✅ `python -c "from app.services.faiss_service import get_faiss_service; print(get_faiss_service().stats())"` shows valid stats
- ✅ Can ingest a medical document and search for it
- ✅ Can ask a question and get a response with sources
- ✅ All responses include medical disclaimers
- ✅ Error responses are user-friendly (no stack traces)

---

## Questions?

This integration is production-ready. Next: Create the FastAPI routes to expose these services via HTTP!
