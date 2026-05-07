"""Chat API endpoints - patient-facing chat, history, feedback, streaming."""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from app.services.chat_service import ChatService
from app.middleware.auth_middleware import get_current_user
from app.extensions import get_db
from app.middleware.rate_limit import limiter
from app.utils.audit import write_audit, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def safe_text(text: str) -> str:
    """UTF-8 round-trip encode/decode with medical symbol replacements."""
    if not isinstance(text, str):
        text = str(text)
    return (
        text.encode("utf-8", "ignore").decode("utf-8")
        .replace("≥", ">=").replace("≤", "<=").replace("°", " degrees")
        .replace("→", "->").replace("•", "-").replace("✓", "OK")
        .replace("✗", "X").replace("⚠", "WARNING").replace("×", "x")
        .replace("÷", "/").replace("±", "+/-").replace("∞", "infinity")
        .replace("√", "sqrt").replace("≈", "~").replace("≠", "!=")
        .replace("©", "(c)").replace("®", "(R)").replace("™", "(TM)")
    )


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
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
    agent_response = service.handle_message(message=message, user_id=current_user["user_id"])

    # Audit logging: PHI access (patient symptoms/queries sent to AI)
    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="send_chat",
        resource_type="chat",
        ip_address=get_client_ip(request),
        details=f"agent={agent_response.get('agent_used')} confidence={agent_response.get('confidence_score')}",
    )

    return {
        "response": safe_text(agent_response.get("response", "")),
        "sources": agent_response.get("sources", []),
        "agent_used": agent_response.get("agent_used", "unknown"),
        "confidence_score": agent_response.get("confidence_score", 0.0),
        "tokens_used": agent_response.get("tokens_used", 0),
        "context_documents_used": agent_response.get("context_documents_used", 0),
        "error": agent_response.get("error", False),
    }


@router.get("/history", response_model=ChatHistoryResponse, status_code=status.HTTP_200_OK)
def get_chat_history(
    request: Request,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatHistoryResponse:
    """Paginated chat history for the current patient."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be >= 0")

    from app.models import Patient
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    history = ChatService(db).get_chat_history(patient_id=patient.id, limit=limit, offset=offset)

    # Audit logging: PHI access (viewing chat history)
    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="view_chat_history",
        resource_type="chat",
        resource_id=patient.id,
        ip_address=get_client_ip(request),
        details=f"limit={limit} offset={offset} total={history['total']}",
    )

    return ChatHistoryResponse(
        items=history["items"],
        total=history["total"],
        limit=limit,
        offset=offset,
        has_next=history["has_next"],
    )


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
def submit_feedback(
    request: Request,
    feedback_request: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Submit thumbs up/down feedback on an AI response."""
    from app.models import Patient
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    success = ChatService(db).submit_feedback(
        chat_id=feedback_request.chat_id,
        patient_id=patient.id,
        feedback=feedback_request.feedback,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Chat message not found")

    # Audit logging: feedback submission
    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="submit_feedback",
        resource_type="chat",
        resource_id=feedback_request.chat_id,
        ip_address=get_client_ip(request),
        details=f"feedback={feedback_request.feedback}",
    )

    return {"success": True, "feedback": feedback_request.feedback}


@router.post("/stream", status_code=status.HTTP_200_OK)
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

    # Log access at start of stream
    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="send_chat_stream",
        resource_type="chat",
        ip_address=get_client_ip(request),
        details="stream_started",
    )

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
                yield f"data: {json.dumps({'type': 'done', 'agent_used': agent_response.get('agent_used'), 'confidence_score': agent_response.get('confidence_score', 0.5), 'sources': agent_response.get('sources', []), 'requires_escalation': bool(agent_response.get('requires_escalation', False)), 'urgency_level': agent_response.get('urgency_level'), 'immediate_action': agent_response.get('immediate_action'), 'emergency_number': agent_response.get('emergency_number')})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': 'Stream failed. Please try again.'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
