"""Chat service - orchestrates AI agents, FAISS, and persistence."""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import ChatHistory, Patient, User
from app.services.euri_service import EuriService
from app.services.faiss_service import FAISSService
from app.agents.orchestrator import OrchestratorAgent
from app.agents.clinical_agent import ClinicalAgent

logger = logging.getLogger(__name__)


class ChatService:
    """
    Orchestrates chat flow: routing → agents → persistence.

    Architecture:
    1. Route receives message, calls handle_message()
    2. Service determines intent (via Orchestrator agent)
    3. Routes to specialist agent (Clinical, RAG, Medication, etc.)
    4. Agent returns response with sources and confidence
    5. Service persists to database
    6. Route returns response to frontend

    Dependency injection:
    - EuriService (singleton): embeddings + LLM
    - FAISSService (singleton): vector search
    - ClinicalAgent (singleton): medical Q&A
    - Database session: passed in __init__
    """

    def __init__(self, db: Session):
        """Initialize with database session.

        Note: Euri, FAISS, and agents are singletons (created once).
        Each request gets the same instances.
        """
        self.db = db
        self.euri = EuriService()
        self.faiss = FAISSService()
        self.orchestrator = OrchestratorAgent()
        self.clinical_agent = ClinicalAgent()

    def handle_message(
        self,
        message: str,
        user_id: str,
        patient_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main chat handler - routes message to appropriate agent.

        Flow:
        1. Get patient info (allergies, medications, medical history)
        2. Get routing intent from Orchestrator
        3. Call appropriate agent
        4. Persist to database
        5. Return response

        Args:
            message: Patient's message
            user_id: User ID from JWT
            patient_id: Optional patient ID (looked up if not provided)

        Returns:
            {
                "response": str,
                "sources": List[Dict],
                "agent_used": str,
                "confidence_score": float,
                "tokens_used": int,
                "context_documents_used": int,
                "error": bool
            }
        """
        try:
            # Step 1: Get patient info
            patient = self._get_patient(user_id, patient_id)
            if not patient:
                logger.warning(f"Patient not found for user {user_id}")
                return self._error_response(
                    "Patient profile not found",
                    agent="error_handler"
                )

            patient_info = self._extract_patient_info(patient)

            logger.info(
                "chat.message.received",
                extra={
                    "user_id": user_id,
                    "patient_id": patient.id,
                    "message_length": len(message),
                }
            )

            # Step 2a: Check for critical symptoms (escalate to triage)
            if self.orchestrator.should_escalate_to_triage(message):
                logger.warning(
                    "chat.critical_symptom_detected",
                    extra={"patient_id": patient.id, "message": message[:100]}
                )
                routing = {
                    "routing_intent": "triage",
                    "agent_to_call": "triage_agent",
                    "confidence": 0.99,
                    "reason": "Critical symptom detected",
                }
            else:
                # Step 2b: Get routing intent
                routing = self._get_routing_intent(message)
            logger.info(
                "chat.message.routed",
                extra={
                    "agent": routing.get("agent_to_call", "unknown"),
                    "confidence": routing.get("confidence", 0.0),
                }
            )

            # Step 3: Route to agent
            agent_response = self._call_agent(
                routing["agent_to_call"],
                message,
                patient_info,
            )

            if agent_response.get("error"):
                logger.warning(
                    "chat.agent_error",
                    extra={"agent": routing["agent_to_call"]}
                )
                return agent_response

            # Step 4: Persist to database
            self._save_chat_history(
                patient.id,
                message,
                agent_response,
            )

            # Step 5: Return response
            logger.info(
                "chat.message.sent",
                extra={
                    "user_id": user_id,
                    "patient_id": patient.id,
                    "agent": agent_response.get("agent_used"),
                    "confidence": agent_response.get("confidence_score"),
                }
            )

            return agent_response

        except Exception as e:
            logger.error(
                f"Chat handler error: {e}",
                exc_info=True,
                extra={"user_id": user_id}
            )
            return self._error_response(
                "Failed to process message",
                agent="error_handler"
            )

    def _get_patient(
        self,
        user_id: str,
        patient_id: Optional[str] = None,
    ) -> Optional[Patient]:
        """Get patient by user_id or patient_id."""
        try:
            if patient_id:
                patient = self.db.query(Patient).filter_by(id=patient_id).first()
            else:
                patient = self.db.query(Patient).filter_by(
                    user_id=user_id
                ).first()
            return patient
        except Exception as e:
            logger.error(f"Failed to get patient: {e}")
            return None

    def _extract_patient_info(self, patient: Patient) -> Dict[str, Any]:
        """Extract relevant patient info for agents."""
        try:
            # Calculate age from DOB
            age = None
            if patient.date_of_birth:
                today = datetime.utcnow().date()
                age = today.year - patient.date_of_birth.year - (
                    (today.month, today.day) < (
                        patient.date_of_birth.month,
                        patient.date_of_birth.day
                    )
                )

            return {
                "patient_id": patient.id,
                "age": age,
                "allergies": (patient.allergies or "").split(","),
                "medications": (patient.current_medications or "").split(","),
                "medical_history": patient.medical_history or "",
                "emergency_contact": patient.emergency_contact,
            }
        except Exception as e:
            logger.warning(f"Failed to extract patient info: {e}")
            return {"patient_id": patient.id}

    def _get_routing_intent(self, message: str) -> Dict[str, Any]:
        """Get routing intent from Orchestrator agent.

        Asks: "What type of question is this?"
        Answers: Clinical, RAG, Medication, Triage, Monitoring, etc.
        """
        try:
            routing = self.orchestrator.route_message(message)
            return routing
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            # Default to clinical
            return {
                "routing_intent": "clinical",
                "agent_to_call": "clinical_agent",
                "confidence": 0.5,
                "fallback": True,
            }

    def _call_agent(
        self,
        agent_name: str,
        message: str,
        patient_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Call specialist agent based on routing.

        Available agents:
        - clinical_agent: Medical Q&A with RAG
        - rag_agent: Document retrieval
        - medication_agent: Drug interactions
        - triage_agent: Urgency assessment
        - monitoring_agent: Vital sign analysis
        - fallback: Generic response
        """
        try:
            if agent_name == "clinical_agent":
                return self.clinical_agent.answer_medical_question(
                    message,
                    patient_info=patient_info,
                )

            elif agent_name == "rag_agent":
                # TODO: Implement RAG agent
                return self.clinical_agent.answer_medical_question(
                    message,
                    patient_info=patient_info,
                )

            elif agent_name == "medication_agent":
                # TODO: Implement medication agent
                return self.clinical_agent.answer_medical_question(
                    message,
                    patient_info=patient_info,
                )

            elif agent_name == "triage_agent":
                # TODO: Implement triage agent
                return self.clinical_agent.answer_medical_question(
                    message,
                    patient_info=patient_info,
                )

            else:
                # Unknown agent, use clinical as fallback
                logger.warning(f"Unknown agent: {agent_name}, using clinical")
                return self.clinical_agent.answer_medical_question(
                    message,
                    patient_info=patient_info,
                )

        except Exception as e:
            logger.error(f"Agent call failed ({agent_name}): {e}")
            return self._error_response(
                "Agent processing failed",
                agent=agent_name,
            )

    def _save_chat_history(
        self,
        patient_id: str,
        user_message: str,
        agent_response: Dict[str, Any],
    ) -> bool:
        """Persist message and response to database."""
        try:
            chat = ChatHistory(
                patient_id=patient_id,
                user_message=user_message,
                ai_response=agent_response.get("response", ""),
                agent_used=agent_response.get("agent_used", "unknown"),
                confidence_score=agent_response.get("confidence_score", 0.5),
                tokens_used=agent_response.get("tokens_used", 0),
            )
            self.db.add(chat)
            self.db.commit()
            logger.info(f"Saved chat history for patient {patient_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")
            self.db.rollback()
            return False

    def _error_response(
        self,
        message: str,
        agent: str = "error_handler",
    ) -> Dict[str, Any]:
        """Return user-friendly error response."""
        return {
            "response": (
                f"{message}. Our team has been notified. "
                "Please try again later."
            ),
            "sources": [],
            "agent_used": agent,
            "confidence_score": 0.0,
            "tokens_used": 0,
            "context_documents_used": 0,
            "error": True,
        }

    # Utility methods for future agents

    def get_chat_history(
        self,
        patient_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get chat history for patient."""
        try:
            query = self.db.query(ChatHistory).filter_by(
                patient_id=patient_id
            ).order_by(ChatHistory.created_at.desc())

            total = query.count()
            items = query.offset(offset).limit(limit).all()

            return {
                "items": [
                    {
                        "id": c.id,
                        "user_message": c.user_message,
                        "ai_response": c.ai_response,
                        "agent_used": c.agent_used,
                        "confidence_score": c.confidence_score,
                        "created_at": c.created_at.isoformat(),
                    }
                    for c in items
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total,
            }

        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_next": False,
            }
