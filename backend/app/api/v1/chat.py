"""Chat API endpoints - POST /api/v1/chat, GET /api/v1/chat/history."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    ChatHistoryQuery,
    ChatHistoryResponse,
    SourceReference,
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from app.services.chat_service import ChatService
from app.middleware.auth_middleware import get_current_user, require_role
from app.extensions import get_db
from app.agents.clinical_agent import get_clinical_agent

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
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send message to medical AI",
    description="Patient sends message to AI orchestrator for medical guidance"
)
def send_message(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    Send message to medical AI.

    The AI will:
    1. Analyze the message (via Orchestrator agent)
    2. Route to appropriate specialist (Clinical, RAG, Medication, etc.)
    3. Retrieve relevant medical documents from knowledge base
    4. Generate evidence-based response with sources

    Args:
        request: ChatRequest with patient message
        current_user: JWT user info (dependency)
        db: Database session (dependency)

    Returns:
        ChatResponse with AI response, sources, and metadata

    Raises:
        400: Invalid input (message too long, etc.)
        401: Not authenticated
        404: Patient profile not found
        503: AI service unavailable
    """
    try:
        # Validate request
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )

        # Initialize service and handle message with safety wrapper
        service = ChatService(db)
        try:
            agent_response = service.handle_message(
                message=request.message.strip(),
                user_id=current_user["user_id"],
            )
        except Exception as e:
            # Catch any service errors and return as ChatResponse
            logger.error("Service error: %s", type(e).__name__)
            return ChatResponse(
                response="Internal processing error. Please try again.",
                sources=[],
                agent_used="error",
                confidence_score=0.0,
                tokens_used=0,
                context_documents_used=0,
                error=True,
            )

        # CRITICAL: Sanitize agent response IMMEDIATELY before any processing
        raw_text = agent_response.get('response', 'Service error')
        response_text = safe_text(raw_text)[:500]

        # Check for errors from service
        if agent_response.get("error"):
            response_text = safe_text(agent_response.get("response", ""))

            return ChatResponse(
                response=response_text,
                sources=[],
                agent_used="clarification",
                confidence_score=0.2,
                tokens_used=0,
                context_documents_used=0,
                error=False,
            )

        # Transform agent response to API response
        sources = [
            SourceReference(
                file=src.get("file", "Unknown"),
                relevance=src.get("relevance", "0%"),
                source_type=src.get("source_type", "text"),
                preview=src.get("preview"),
            )
            for src in agent_response.get("sources", [])
        ]

        return ChatResponse(
            response=response_text,
            sources=sources,
            agent_used=agent_response.get("agent_used", "orchestrator"),
            confidence_score=agent_response.get("confidence_score", 0.5),
            tokens_used=agent_response.get("tokens_used", 0),
            context_documents_used=agent_response.get("context_documents_used", 0),
            error=False,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, auth failures)
        raise

    except Exception as e:
        # Catch-all: return error ChatResponse instead of raising
        error_type = type(e).__name__
        logger.error("Unexpected error in chat: %s", error_type)

        return ChatResponse(
            response="An error occurred processing your message. Please try again.",
            sources=[],
            agent_used="error",
            confidence_score=0.0,
            tokens_used=0,
            context_documents_used=0,
            error=True,
        )


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
