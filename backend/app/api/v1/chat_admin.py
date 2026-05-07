"""Chat admin endpoints - document ingestion and service health check."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.chat_schema import IngestDocumentRequest, IngestDocumentResponse
from app.services.chat_service import ChatService
from app.middleware.auth_middleware import require_role
from app.extensions import get_db
from app.agents.clinical_agent import get_clinical_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)) -> dict:
    """Check health of chat service dependencies (Euri, FAISS, database)."""
    try:
        service = ChatService(db)

        euri_health = None
        try:
            euri_health = service.euri.health_check()
        except Exception as e:
            logger.error(f"Euri health check failed: {e}")
            euri_health = {"status": "unavailable", "embedding_api": False, "llm_api": False, "error": str(e)}

        faiss_ok = False
        try:
            faiss_ok = service.faiss.health_check()
        except Exception as e:
            logger.warning(f"FAISS health check failed: {e}")

        db_ok = False
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            db_ok = True
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")

        euri_ok = euri_health and euri_health["status"] == "healthy"
        return {
            "status": "healthy" if (euri_ok and faiss_ok and db_ok) else "degraded",
            "services": {"euri": euri_health, "faiss": faiss_ok, "database": db_ok},
        }

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "error", "services": {"euri": False, "faiss": False, "database": False}}


@router.post(
    "/ingest",
    response_model=IngestDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def ingest_medical_document(
    request: IngestDocumentRequest,
    current_user: dict = Depends(require_role("admin")),
) -> IngestDocumentResponse:
    """Ingest medical document into FAISS knowledge base (admin only)."""
    try:
        agent = get_clinical_agent()
        result = agent.ingest_medical_document(
            content=request.content,
            source_type=request.source_type,
            source_name=request.source_name,
            metadata={"ingested_by": current_user["user_id"]},
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Document ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Failed to ingest document. Please check format and try again.")
