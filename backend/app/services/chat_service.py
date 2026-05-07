"""Chat service — intent routing, agent dispatch, and response assembly."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models import Patient
from app.services.euri_service import get_euri_service
from app.services.faiss_service import get_faiss_service
from app.services.chat_history_service import ChatHistoryService
from app.agents.orchestrator import get_orchestrator_agent
from app.agents.clinical_agent import get_clinical_agent
from app.agents.triage_agent import get_triage_agent
from app.agents.medication_agent import get_medication_agent
from app.agents.monitoring_agent import get_monitoring_agent
from app.utils.chat_extractors import extract_medications, extract_vitals_from_message

logger = logging.getLogger(__name__)

_UNICODE_MAP = {
    '≥': '>=', '≤': '<=', '°': ' degrees', '→': '->', '•': '-', '♥': '*',
    '✓': 'OK', '✗': 'X', '⚠': 'WARNING', '×': 'x', '÷': '/', '±': '+/-',
    '∞': 'infinity', '√': 'sqrt', '≈': '~', '≠': '!=',
    '©': '(c)', '®': '(R)', '™': '(TM)',
}


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.euri = get_euri_service()
        self.faiss = get_faiss_service()
        self.orchestrator = get_orchestrator_agent()
        self.clinical_agent = get_clinical_agent()
        self.triage_agent = get_triage_agent()
        self.medication_agent = get_medication_agent()
        self.monitoring_agent = get_monitoring_agent()
        self._history = ChatHistoryService(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def handle_message(self, message: str, user_id: str, patient_id: Optional[str] = None) -> Dict[str, Any]:
        """Route message to the appropriate agent and persist the exchange."""
        try:
            patient = self._get_patient(user_id, patient_id)
            if not patient:
                return self._error_response("Patient profile not found")

            patient_info = self._extract_patient_info(patient)

            if self.orchestrator.should_escalate_to_triage(message):
                routing = {"agent_to_call": "triage_agent", "confidence": 0.99}
            else:
                routing = self._get_routing_intent(message)

            agent_response = self._call_agent(routing["agent_to_call"], message, patient_info)

            if "response" in agent_response and agent_response["response"]:
                agent_response["response"] = self._sanitize(str(agent_response["response"]))

            if not agent_response.get("error"):
                self._history.save(patient.id, message, agent_response)

            return agent_response

        except UnicodeEncodeError:
            logger.error("Unicode encoding error in chat", extra={"user_id": user_id})
            return self._error_response("Character encoding error. Please try again.")
        except Exception as e:
            logger.error(f"Chat handler error: {str(e)[:100]}", extra={"user_id": user_id})
            return self._error_response("Failed to process message")

    def get_chat_history(self, patient_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        return self._history.get_history(patient_id, limit, offset)

    def submit_feedback(self, chat_id: str, patient_id: str, feedback: str) -> bool:
        return self._history.submit_feedback(chat_id, patient_id, feedback)

    # kept for stream endpoint in chat.py which calls these directly
    def _save_chat_history(self, patient_id: str, user_message: str, agent_response: Dict[str, Any]) -> bool:
        return self._history.save(patient_id, user_message, agent_response)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_patient(self, user_id: str, patient_id: Optional[str] = None) -> Optional[Patient]:
        try:
            if patient_id:
                return self.db.query(Patient).filter_by(id=patient_id).first()
            return self.db.query(Patient).filter_by(user_id=user_id).first()
        except Exception as e:
            logger.error(f"Failed to get patient: {e}")
            return None

    def _extract_patient_info(self, patient: Patient) -> Dict[str, Any]:
        try:
            age = None
            if patient.date_of_birth:
                today = datetime.utcnow().date()
                age = today.year - patient.date_of_birth.year - (
                    (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day)
                )
            from app.models import Vitals
            rv = None
            try:
                rv = self.db.query(Vitals).filter_by(patient_id=patient.id).order_by(Vitals.created_at.desc()).first()
            except Exception:
                pass
            return {
                "patient_id": patient.id,
                "age": age,
                "allergies": (patient.allergies or "").split(","),
                "medications": (patient.current_medications or "").split(","),
                "medical_history": patient.medical_history or "",
                "emergency_contact": patient.emergency_contact,
                "recent_vitals": {
                    "heart_rate": rv.heart_rate, "blood_pressure_systolic": rv.blood_pressure_systolic,
                    "blood_pressure_diastolic": rv.blood_pressure_diastolic, "temperature": rv.temperature,
                    "oxygen_saturation": rv.oxygen_saturation, "respiratory_rate": rv.respiratory_rate,
                    "weight": rv.weight, "timestamp": rv.created_at.isoformat(),
                } if rv else None,
            }
        except Exception as e:
            logger.warning(f"Failed to extract patient info: {e}")
            return {"patient_id": patient.id}

    def _get_routing_intent(self, message: str) -> Dict[str, Any]:
        try:
            return self.orchestrator.route_message(message)
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return {"agent_to_call": "clinical_agent", "confidence": 0.5, "fallback": True}

    def _call_agent(self, agent_name: str, message: str, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if agent_name in ("clinical_agent", "rag_agent"):
                resp = self.clinical_agent.answer_medical_question(message, patient_info=patient_info)
                if "response" in resp:
                    resp["response"] = self._sanitize(str(resp["response"]))
                return resp

            if agent_name == "triage_agent":
                return self.triage_agent.assess_urgency(message, patient_info=patient_info)

            if agent_name == "medication_agent":
                meds = extract_medications(message)
                if len(meds) > 1:
                    return self.medication_agent.check_medication_interactions(meds, patient_info=patient_info)
                return self.medication_agent.check_single_medication(
                    meds[0] if meds else "medication", patient_info=patient_info
                )

            if agent_name == "monitoring_agent":
                vitals = extract_vitals_from_message(message)
                if not vitals and patient_info and patient_info.get("recent_vitals"):
                    rv = patient_info["recent_vitals"]
                    vitals = {k: v for k, v in rv.items() if k != "timestamp" and v is not None}
                if vitals:
                    return self.monitoring_agent.analyze_vitals(vitals, patient_info=patient_info)
                return self._error_response(
                    "No vital measurements found. Record vitals on the Vitals page or include values in your message.",
                    agent="monitoring_agent",
                )

            # Unknown agent — fall back to clinical
            logger.warning(f"Unknown agent '{agent_name}', falling back to clinical")
            return self.clinical_agent.answer_medical_question(message, patient_info=patient_info)

        except Exception as e:
            logger.error(f"Agent call failed ({agent_name}): {str(e)[:200]}")
            return self._error_response("Agent processing failed", agent=agent_name)

    def _sanitize(self, text: str) -> str:
        if not text:
            return text
        result = str(text)
        for src, dst in _UNICODE_MAP.items():
            result = result.replace(src, dst)
        return result

    def _sanitize_response(self, text: str) -> str:
        return self._sanitize(text)

    def _error_response(self, message: str, agent: str = "error_handler") -> Dict[str, Any]:
        return {
            "response": self._sanitize(f"{message}. Our team has been notified. Please try again later."),
            "sources": [],
            "agent_used": agent,
            "confidence_score": 0.0,
            "tokens_used": 0,
            "context_documents_used": 0,
            "error": True,
        }
