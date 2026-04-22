# Error Handling: Euri API + FAISS Integration

> Production-ready error handling with graceful degradation and retry logic

---

## Error Hierarchy

```
APIError (from OpenAI SDK)
├── RateLimitError        → Exponential backoff + retry
├── APIConnectionError    → Fallback to cached or degraded response
├── AuthenticationError   → Check EURI_API_KEY immediately
└── APITimeoutError       → Retry with increased timeout

FAISSException
├── Index corruption      → Reinitialize from backup
├── Disk space full       → Clean old vectors
└── Search timeout        → Reduce top_k

ValidationError
├── Invalid embedding     → Log + alert engineering
├── Invalid metadata      → Sanitize + log
└── Invalid response      → Parse error handling
```

---

## Euri API Error Handling

### Embedding Failures

```python
# app/services/euri_service.py

from tenacity import retry, stop_after_attempt, wait_exponential
from openai import APIError, RateLimitError, AuthenticationError

class EuriService:
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_text(self, text: str) -> List[float]:
        """
        Embed text with automatic retry on transient failures.
        
        Retries on:
        - RateLimitError (429) → exponential backoff
        - APIConnectionError → connection issues
        - APITimeoutError → timeout (retry)
        
        Does NOT retry on:
        - AuthenticationError → credentials invalid
        - ValidationError → input too long
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                dimensions=768,
            )
            return response.data[0].embedding
        
        except RateLimitError as e:
            # Will auto-retry by tenacity
            logger.warning(f"Rate limited (429): {e}")
            raise
        
        except AuthenticationError as e:
            # Cannot retry - API key invalid
            logger.critical(f"Auth failed - check EURI_API_KEY: {e}")
            raise ValueError("Invalid Euri API credentials") from e
        
        except APIConnectionError as e:
            # Network issue - will retry
            logger.warning(f"Connection failed: {e}")
            raise
        
        except APIError as e:
            # Other API errors
            logger.error(f"Euri API error: {e}")
            if "context length" in str(e).lower():
                raise ValueError("Input text too long (max 8192 tokens)") from e
            raise
```

### LLM Generation Failures

```python
def generate_medical_response(
    self,
    patient_question: str,
    medical_context: str,
    patient_info: Optional[Dict] = None,
    stream: bool = False,
) -> str:
    """Generate medical response with error handling."""
    try:
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": self._build_system_prompt(patient_info)},
                {"role": "user", "content": medical_context + patient_question},
            ],
            temperature=0.3,
            max_tokens=2048,
            stream=stream,
        )
        return response.choices[0].message.content
    
    except RateLimitError:
        logger.warning("LLM rate limited - returning fallback")
        return (
            "The AI service is experiencing high load. "
            "Please try again in a moment."
        )
    
    except AuthenticationError:
        logger.critical("LLM auth failed - check EURI_API_KEY")
        raise ValueError("Medical AI service authentication failed")
    
    except APIConnectionError:
        logger.error("LLM connection lost - returning degraded response")
        return (
            "Connection to medical AI service lost. "
            "Returning basic information only."
        )
    
    except APIError as e:
        logger.error(f"LLM generation failed: {e}")
        raise
```

### Health Check with Fallback

```python
def health_check(self) -> Dict[str, bool]:
    """
    Test Euri API health with service-specific checks.
    
    Returns:
    {
        "euri_embedding": True,
        "euri_llm": True,
        "overall": True
    }
    """
    results = {
        "euri_embedding": False,
        "euri_llm": False,
    }
    
    # Test embeddings
    try:
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input="Health check",
            dimensions=768,
        )
        results["euri_embedding"] = len(response.data[0].embedding) == 768
    except Exception as e:
        logger.warning(f"Euri embedding health check failed: {e}")
    
    # Test LLM
    try:
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
        )
        results["euri_llm"] = response.choices[0].message.content is not None
    except Exception as e:
        logger.warning(f"Euri LLM health check failed: {e}")
    
    results["overall"] = results["euri_embedding"] and results["euri_llm"]
    return results
```

---

## FAISS Error Handling

### Search Failures

```python
# app/services/faiss_service.py

def search_medical_context(
    self,
    query_embedding: List[float],
    top_k: int = 5,
) -> List[Dict]:
    """Search with error handling."""
    try:
        if self.index.ntotal == 0:
            logger.warning("FAISS index is empty - no documents to search")
            return []
        
        query = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query, top_k)
        
        # Process results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # Invalid index
                continue
            
            meta = self.metadata.get(int(idx))
            if not meta or meta.get("deleted"):  # Skip deleted docs
                continue
            
            results.append({
                "id": int(idx),
                "score": 1.0 / (1.0 + float(distance)),  # L2 distance to similarity
                "metadata": meta,
            })
        
        return results
    
    except Exception as e:
        logger.error(f"FAISS search failed: {e}")
        return []  # Return empty results - graceful degradation
```

### Index Corruption Recovery

```python
def recover_from_corruption(self) -> bool:
    """
    Attempt to recover corrupted FAISS index.
    
    Strategy:
    1. Try to validate current index
    2. If invalid, check for backup
    3. If no backup, reinitialize empty
    """
    try:
        # Test current index
        test_vector = np.array([[0.0] * 768], dtype=np.float32)
        self.index.search(test_vector, 1)
        logger.info("FAISS index is valid")
        return True
    
    except Exception as e:
        logger.error(f"FAISS index corrupted: {e}")
        
        # Check for backup
        backup_file = self.index_file + ".backup"
        if os.path.exists(backup_file):
            logger.info("Restoring from backup...")
            try:
                self.index = faiss.read_index(backup_file)
                logger.info("Restored from backup")
                return True
            except Exception as backup_e:
                logger.error(f"Backup also corrupted: {backup_e}")
        
        # Last resort: reinitialize
        logger.warning("Reinitializing FAISS index (data loss!)")
        self.index = faiss.IndexFlatL2(self.embedding_dimensions)
        self._save_index()
        return False
```

### Disk Space Handling

```python
def check_disk_space(self) -> Dict[str, Any]:
    """Monitor disk usage and clean if necessary."""
    import shutil
    
    total, used, free = shutil.disk_usage(self.index_path)
    usage_percent = (used / total) * 100
    
    return {
        "total_gb": total / (1024**3),
        "used_gb": used / (1024**3),
        "free_gb": free / (1024**3),
        "usage_percent": usage_percent,
        "need_cleanup": usage_percent > 80,
    }

def cleanup_old_vectors(self, days: int = 30) -> int:
    """Delete vectors older than N days."""
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    deleted = 0
    
    for doc_id, meta in list(self.metadata.items()):
        try:
            timestamp = datetime.fromisoformat(meta["timestamp"])
            if timestamp < cutoff:
                self.delete_document(doc_id)
                deleted += 1
        except Exception as e:
            logger.warning(f"Failed to clean doc {doc_id}: {e}")
    
    logger.info(f"Cleaned {deleted} old vectors")
    return deleted
```

---

## Service Layer Error Handling

### ChatService with Fallback

```python
# app/services/chat_service.py

class ChatService:
    
    def handle_message(
        self,
        message: str,
        user_id: str,
        patient_id: str,
    ) -> Dict[str, Any]:
        """
        Handle chat message with comprehensive error handling.
        
        Fallback chain:
        1. Try full RAG pipeline
        2. If fails, try LLM without context
        3. If fails, return cached response
        4. If no cache, return error message
        """
        try:
            # Step 1: Route to agent
            intent = self._get_routing_intent(message)
            logger.info(f"Routed to: {intent['agent_to_call']}")
            
            # Step 2: Get agent response
            if intent["agent_to_call"] == "clinical":
                response = self.clinical_agent.answer_medical_question(
                    message,
                    patient_info=self._get_patient_info(patient_id),
                )
            else:
                # Other agents...
                response = self._get_fallback_response(message)
            
            # Step 3: Save to database
            try:
                chat = ChatHistory(
                    patient_id=patient_id,
                    user_message=message,
                    ai_response=response["response"],
                    agent_used=response.get("agent_used", "unknown"),
                    confidence_score=response.get("confidence_score", 0.5),
                    tokens_used=response.get("tokens_used", 0),
                )
                self.db.add(chat)
                self.db.commit()
            except Exception as db_e:
                logger.error(f"Failed to save chat history: {db_e}")
                self.db.rollback()
                # Continue - don't fail user request due to logging error
            
            return response
        
        except Exception as e:
            logger.error(f"Chat handling failed: {e}")
            return self._get_error_response(e)
    
    def _get_routing_intent(self, message: str) -> Dict:
        """Get routing with fallback."""
        try:
            return self.euri.generate_orchestrator_response(message)
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            # Default to clinical agent
            return {
                "routing_intent": "clinical",
                "confidence": 0.5,
                "agent_to_call": "clinical_agent",
                "fallback": True,
            }
    
    def _get_patient_info(self, patient_id: str) -> Dict:
        """Get patient info with error handling."""
        try:
            patient = self.db.query(Patient).filter_by(id=patient_id).first()
            if not patient:
                return {}
            
            return {
                "patient_id": patient.id,
                "age": self._calculate_age(patient.date_of_birth),
                "allergies": patient.allergies or "",
                "medications": patient.current_medications or "",
                "history": patient.medical_history or "",
            }
        except Exception as e:
            logger.warning(f"Failed to get patient info: {e}")
            return {}
    
    def _get_error_response(self, error: Exception) -> Dict:
        """Return user-friendly error response."""
        logger.error(f"Chat error: {error}")
        
        error_type = type(error).__name__
        
        if "AuthenticationError" in error_type:
            message = "Medical AI service is unavailable. Please try again later."
        elif "RateLimitError" in error_type:
            message = "AI service is busy. Please wait a moment and try again."
        elif "ConnectionError" in error_type:
            message = "Network connection error. Please check your connection."
        else:
            message = "An error occurred. Our team has been notified. Please try again."
        
        return {
            "response": message,
            "error": True,
            "agent_used": "error_handler",
            "confidence_score": 0.0,
            "tokens_used": 0,
        }
```

---

## API Route Error Handling

### Chat Endpoint with Status Codes

```python
# app/api/v1/chat.py

@router.post("/api/v1/chat", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send message to medical AI."""
    try:
        # Validate request
        if len(request.message) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Message too long (max 1000 chars)"
            )
        
        # Get patient
        patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient profile not found")
        
        # Process message
        service = ChatService(db)
        response = service.handle_message(
            request.message,
            current_user["user_id"],
            patient.id,
        )
        
        # Check for errors
        if response.get("error"):
            return ChatResponse(
                response=response["response"],
                agent_used=response.get("agent_used", "error"),
                confidence_score=0.0,
                sources=[],
                error=True,
            ), 503  # Service Unavailable
        
        return ChatResponse(
            response=response["response"],
            agent_used=response.get("agent_used", "unknown"),
            confidence_score=response.get("confidence_score", 0.5),
            sources=response.get("sources", []),
            tokens_used=response.get("tokens_used", 0),
        )
    
    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except NotFoundError as e:
        logger.warning(f"Not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

---

## Monitoring & Alerting

### Health Check Endpoint

```python
@router.get("/api/v1/health")
def health_check(db: Session = Depends(get_db)):
    """System health status."""
    try:
        euri_health = get_euri_service().health_check()
        faiss_health = get_faiss_service().health_check()
        
        # Database check
        db.execute("SELECT 1")
        db_healthy = True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_healthy = False
    
    all_healthy = (
        euri_health["overall"] and
        faiss_health and
        db_healthy
    )
    
    status_code = 200 if all_healthy else 503
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "euri_embedding": euri_health["euri_embedding"],
            "euri_llm": euri_health["euri_llm"],
            "faiss": faiss_health,
            "database": db_healthy,
        },
        "version": "0.1.0",
    }, status_code
```

---

## Testing Error Scenarios

```python
# backend/tests/test_error_handling.py

import pytest
from unittest.mock import patch, MagicMock

def test_euri_rate_limit_retry():
    """Test retry on rate limit."""
    from app.services.euri_service import EuriService
    from openai import RateLimitError
    
    service = EuriService()
    
    with patch.object(service.client.embeddings, 'create') as mock:
        # First 2 calls fail, 3rd succeeds
        mock.side_effect = [
            RateLimitError("429"),
            RateLimitError("429"),
            MagicMock(data=[MagicMock(embedding=[0.1] * 768)])
        ]
        
        result = service.embed_text("test")
        assert len(result) == 768
        assert mock.call_count == 3  # Verified retries


def test_faiss_empty_index_search():
    """Test search on empty index."""
    from app.services.faiss_service import FAISSService
    
    service = FAISSService()
    service.index.ntotal = 0  # Empty
    
    results = service.search_medical_context([0.1] * 768)
    assert results == []


def test_chat_service_fallback():
    """Test fallback when Euri fails."""
    from app.services.chat_service import ChatService
    from openai import APIError
    
    service = ChatService(db=MagicMock())
    
    with patch.object(service.euri, 'generate_orchestrator_response') as mock:
        mock.side_effect = APIError("API down")
        
        response = service.handle_message("test", "user123", "patient123")
        assert response["error"] == True
        assert "unavailable" in response["response"].lower()
```

---

## Key Principles

1. **Fail gracefully** - never crash; return degraded response
2. **Retry transient errors** - rate limits, network, timeouts
3. **Don't retry permanent errors** - auth, validation, not found
4. **Log everything** - errors, fallbacks, degradation
5. **Health checks** - monitor service availability
6. **User-friendly messages** - never expose internal errors
7. **Fallback chain** - RAG → LLM without context → cached → error message
8. **Data integrity** - always persist successfully processed messages
