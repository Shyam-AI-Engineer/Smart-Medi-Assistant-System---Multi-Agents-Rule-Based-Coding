"""Chat API endpoints - POST /api/v1/chat, GET /api/v1/chat/history."""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    ChatHistoryQuery,
    ChatHistoryResponse,
    SourceReference,
    IngestDocumentRequest,
    IngestDocumentResponse,
    FeedbackRequest,
)
from app.services.chat_service import ChatService
from app.middleware.auth_middleware import get_current_user, require_role
from app.extensions import get_db
from app.agents.clinical_agent import get_clinical_agent
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def safe_text(text: str) -> str:
    """Sanitize text: UTF-8 round-trip encode/decode with problem char replacements."""
    if not isinstance(text, str):
        text = str(text)

    # UTF-8 round-trip to catch encoding issues
    return (
        text.encode("utf-8", "ignore").decode("utf-8")
        .replace("≥", ">=")
        .replace("≤", "<=")
        .replace("°", " degrees")
        .replace("→", "->")
        .replace("•", "-")
        .replace("✓", "OK")
        .replace("✗", "X")
        .replace("⚠", "WARNING")
        .replace("×", "x")
        .replace("÷", "/")
        .replace("±", "+/-")
        .replace("∞", "infinity")
        .replace("√", "sqrt")
        .replace("≈", "~")
        .replace("≠", "!=")
        .replace("©", "(c)")
        .replace("®", "(R)")
        .replace("™", "(TM)")
    )


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Send message to medical AI",
    description="Patient sends message to AI orchestrator for medical guidance"
)
@limiter.limit("10/minute")
def send_message(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Send message to medical AI."""
    message = chat_request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    service = ChatService(db)
    agent_response = service.handle_message(
        message=message,
        user_id=current_user["user_id"],
    )

    response_text = safe_text(agent_response.get("response", ""))

    return {
        "response": response_text,
        "sources": agent_response.get("sources", []),
        "agent_used": agent_response.get("agent_used", "unknown"),
        "confidence_score": agent_response.get("confidence_score", 0.0),
        "tokens_used": agent_response.get("tokens_used", 0),
        "context_documents_used": agent_response.get("context_documents_used", 0),
        "error": agent_response.get("error", False),
    }


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get chat history",
    description="Retrieve conversation history for current patient"
)
def get_chat_history(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    """
    Get chat history for current user.

    Note: Patients can only see their own history.
    Doctors/admins can see assigned/all patients respectively.

    Args:
        limit: Max messages to return (1-100, default 20)
        offset: Skip N messages for pagination (default 0)
        current_user: JWT user info (dependency)
        db: Database session (dependency)

    Returns:
        ChatHistoryResponse with paginated messages

    Raises:
        400: Invalid pagination parameters
        401: Not authenticated
        404: Patient profile not found
    """
    try:
        # Validate pagination
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )

        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offset must be >= 0"
            )

        # Get patient for current user
        from app.models import Patient
        patient = db.query(Patient).filter_by(
            user_id=current_user["user_id"]
        ).first()

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found"
            )

        # Get history via service
        service = ChatService(db)
        history = service.get_chat_history(
            patient_id=patient.id,
            limit=limit,
            offset=offset,
        )

        return ChatHistoryResponse(
            items=history["items"],
            total=history["total"],
            limit=limit,
            offset=offset,
            has_next=history["has_next"],
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting chat history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )


@router.post(
    "/feedback",
    status_code=status.HTTP_200_OK,
    summary="Submit feedback on chat response",
    description="Patient submits thumbs up/down feedback on an AI response"
)
@limiter.limit("30/minute")
def submit_feedback(
    request: Request,
    feedback_request: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Patient submits feedback (thumbs up/down) on an AI response.

    Args:
        feedback_request: Contains chat_id and feedback type
        current_user: JWT user info (dependency)
        db: Database session (dependency)

    Returns:
        {"success": True, "feedback": "thumbs_up" | "thumbs_down"}

    Raises:
        404: Chat message not found or doesn't belong to patient
        400: Invalid feedback type
    """
    try:
        from app.models import Patient

        # Get patient for current user
        patient = db.query(Patient).filter_by(
            user_id=current_user["user_id"]
        ).first()

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found"
            )

        # Submit feedback
        service = ChatService(db)
        success = service.submit_feedback(
            chat_id=feedback_request.chat_id,
            patient_id=patient.id,
            feedback=feedback_request.feedback,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat message not found"
            )

        return {"success": True, "feedback": feedback_request.feedback}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit feedback"
        )


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Chat service health check",
    description="Check if chat service and dependencies are healthy"
)
def health_check(db: Session = Depends(get_db)) -> dict:
    """
    Check health of chat service and dependencies.

    Tests:
    - Euri API (embeddings + LLM)
    - FAISS vector database
    - Database connection

    Returns:
        {
            "status": "healthy" | "degraded",
            "services": {
                "euri": bool,
                "faiss": bool,
                "database": bool
            }
        }
    """
    try:
        service = ChatService(db)

        # Check Euri
        euri_ok = False
        try:
            euri_ok = bool(service.euri.health_check())
        except Exception as e:
            logger.warning(f"Euri health check failed: {e}")

        # Check FAISS
        faiss_ok = False
        try:
            faiss_ok = service.faiss.health_check()
        except Exception as e:
            logger.warning(f"FAISS health check failed: {e}")

        # Check database
        db_ok = False
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            db_ok = True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")

        overall = euri_ok and faiss_ok and db_ok

        return {
            "status": "healthy" if overall else "degraded",
            "services": {
                "euri": euri_ok,
                "faiss": faiss_ok,
                "database": db_ok,
            },
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "services": {
                "euri": False,
                "faiss": False,
                "database": False,
            },
        }


@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Stream message to medical AI",
    description="Same as /chat but streams tokens as SSE for progressive rendering",
)
@limiter.limit("10/minute")
def send_message_stream(
    request: Request,
    chat_request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Stream AI response as Server-Sent Events."""
    message = chat_request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    service = ChatService(db)

    def generate():
        try:
            patient = service._get_patient(current_user["user_id"])
            if not patient:
                yield f"data: {json.dumps({'type': 'error', 'content': 'Patient profile not found'})}\n\n"
                return

            patient_info = service._extract_patient_info(patient)

            if service.orchestrator.should_escalate_to_triage(message):
                routing = {"agent_to_call": "triage_agent", "confidence": 0.99}
            else:
                routing = service._get_routing_intent(message)

            agent_name = routing.get("agent_to_call", "clinical_agent")
            yield f"data: {json.dumps({'type': 'agent', 'agent': agent_name})}\n\n"

            if agent_name in ("clinical_agent", "rag_agent"):
                stream, metadata = service.clinical_agent.answer_medical_question_stream(
                    message, patient_info=patient_info
                )

                if stream is None:
                    yield f"data: {json.dumps({'type': 'error', 'content': 'AI service unavailable'})}\n\n"
                    return

                full_response = ""
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        full_response += delta
                        yield f"data: {json.dumps({'type': 'token', 'content': delta})}\n\n"

                sanitized = service._sanitize_response(full_response)
                service._save_chat_history(patient.id, message, {
                    "response": sanitized,
                    "agent_used": metadata.get("agent_used", "clinical"),
                    "confidence_score": metadata.get("confidence_score", 0.8),
                    "tokens_used": 0,
                })
                yield f"data: {json.dumps({'type': 'done', **metadata})}\n\n"

            else:
                agent_response = service._call_agent(agent_name, message, patient_info)
                response_text = agent_response.get("response", "")
                if "response" in agent_response:
                    agent_response["response"] = service._sanitize_response(response_text)

                words = response_text.split(" ")
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

                service._save_chat_history(patient.id, message, agent_response)
                yield f"data: {json.dumps({'type': 'done', 'agent_used': agent_response.get('agent_used'), 'confidence_score': agent_response.get('confidence_score', 0.5), 'sources': agent_response.get('sources', [])})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': 'Stream failed. Please try again.'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/ingest",
    response_model=IngestDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest medical document",
    description="Add medical document to knowledge base (admin only)"
)
def ingest_medical_document(
    request: IngestDocumentRequest,
    current_user: dict = Depends(require_role("admin")),
) -> IngestDocumentResponse:
    """
    Ingest medical document into FAISS knowledge base.

    Restricted to admin users. Embeds document and adds to vector database.

    Args:
        request: Document content, type, and name
        current_user: Admin user (JWT validated)
        db: Database session

    Returns:
        IngestDocumentResponse with document ID and ingestion status

    Raises:
        400: Invalid input (content too short, invalid source_type)
        401: Not authenticated
        403: User not admin
    """
    try:
        logger.info(
            f"Ingesting document: {request.source_name} "
            f"(by user {current_user['user_id']})"
        )

        agent = get_clinical_agent()
        result = agent.ingest_medical_document(
            content=request.content,
            source_type=request.source_type,
            source_name=request.source_name,
            metadata={"ingested_by": current_user["user_id"]},
        )

        logger.info(
            f"Document ingested successfully: {request.source_name} "
            f"(ID: {result.get('document_id')})"
        )

        return IngestDocumentResponse(
            success=result.get("success", False),
            document_id=result.get("document_id"),
            document_name=result.get("document_name", request.source_name),
            chunks_added=result.get("chunks_added", 1),
            tokens_processed=result.get("tokens_processed"),
            message=result.get("message", "Document ingested"),
        )

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Document ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to ingest document. Please check format and try again."
        )
