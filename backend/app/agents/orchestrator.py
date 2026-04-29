"""Orchestrator Agent - routes patient queries to specialist agents.

This agent:
1. Analyzes patient message intent
2. Determines which specialist agent should handle it
3. Routes to: Clinical, RAG, Medication, or Triage agent
4. Returns routing decision with confidence score

Follows clean architecture: delegates to EuriService for LLM.
"""

import logging
from typing import Optional, List, Dict, Any
from app.services.euri_service import get_euri_service

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Routes medical queries to appropriate specialist agents."""

    def __init__(self):
        """Initialize orchestrator with Euri service."""
        self.euri = get_euri_service()
        self.agent_name = "orchestrator"

    def route_message(
        self,
        patient_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze patient message and route to specialist agent.

        Flow:
        1. Check for vital sign keywords (monitoring agent)
        2. Check for critical symptoms (triage agent)
        3. Call Euri LLM to analyze intent for other queries
        4. Extract routing decision (agent_to_call, confidence, reason)
        5. Return routing result

        Args:
            patient_message: Patient's question or statement
            chat_history: Previous conversation messages (for context)

        Returns:
            {
                "routing_intent": "clinical|medication|triage|rag|monitoring",
                "confidence": 0.95,
                "reason": "User asked about symptom interactions",
                "agent_to_call": "medication_agent|monitoring_agent",
                "suggested_context": "Patient with high blood pressure"
            }
        """
        try:
            message_lower = patient_message.lower()

            # Step 1: Check for treatment/symptom queries (route to clinical agent with FAISS)
            # These should be answered with medical knowledge base documents
            treatment_keywords = [
                "treatment for", "how to treat", "how do i treat",
                "cure for", "what helps", "what should i do for",
                "remedy for", "best way to treat", "what medicine",
                "what drug", "treat my", "treatment of"
            ]
            if any(keyword in message_lower for keyword in treatment_keywords):
                logger.info("Treatment query detected - routing to clinical_agent with FAISS")
                return {
                    "routing_intent": "clinical",
                    "confidence": 0.98,
                    "reason": "User asked for treatment recommendations",
                    "agent_to_call": "clinical_agent",
                }

            # Step 2: Check for medication safety/interaction keywords (rule-based lookup)
            medication_keywords = [
                "medication", "drug", "pill", "tablet",
                "interaction", "contraindication", "side effect",
                "can i take", "is it safe to take",
                "taking", "currently on"
            ]
            if any(keyword in message_lower for keyword in medication_keywords):
                logger.info("Medication query detected - routing to medication_agent")
                return {
                    "routing_intent": "medication",
                    "confidence": 0.98,
                    "reason": "User asked about medications or drugs",
                    "agent_to_call": "medication_agent",
                }

            # Step 2: Check for vital sign keywords (fast path)
            # NOTE: Does NOT include "fever" or "temperature" as keywords to avoid
            # routing treatment questions to monitoring agent
            vital_keywords = [
                "heart rate", "pulse", "bp", "blood pressure",
                "oxygen", "spo2", "respiratory rate", "breathing", "vitals",
                "measure", "record vitals", "my heart rate is", "my bp is"
            ]
            if any(keyword in message_lower for keyword in vital_keywords):
                logger.info("Vital sign query detected - routing to monitoring_agent")
                return {
                    "routing_intent": "monitoring",
                    "confidence": 0.98,
                    "reason": "User asked about vital signs",
                    "agent_to_call": "monitoring_agent",
                }

            logger.info(f"Orchestrator routing message: {patient_message[:100]}...")

            # Step 3: Call Euri to determine routing for general queries
            routing_result = self.euri.generate_orchestrator_response(
                user_message=patient_message,
                chat_history=chat_history,
            )

            logger.info(
                f"Routed to {routing_result.get('agent_to_call')} "
                f"with confidence {routing_result.get('confidence'):.2f}"
            )

            return routing_result

        except Exception as e:
            logger.error(f"Orchestrator routing failed: {e}")
            # Fallback: route to clinical agent
            fallback_result = {
                "routing_intent": "clinical",
                "confidence": 0.5,
                "reason": "Fallback routing due to error",
                "agent_to_call": "clinical_agent",
                "error": str(e),
                "fallback": True,
            }
            return fallback_result

    def should_escalate_to_triage(
        self,
        patient_message: str,
    ) -> bool:
        """
        Check if message contains critical symptoms requiring triage.

        Keywords: chest pain, difficulty breathing, loss of consciousness, severe bleeding, etc.
        """
        critical_keywords = [
            "chest pain",
            "difficulty breathing",
            "shortness of breath",
            "can't breathe",
            "lose consciousness",
            "unconscious",
            "severe bleeding",
            "choking",
            "severe poisoning",
            "seizure",
            "stroke symptoms",
            "severe allergic reaction",
            "anaphylaxis",
            "suicide",
            "self-harm",
        ]

        message_lower = patient_message.lower()
        for keyword in critical_keywords:
            if keyword in message_lower:
                logger.warning(f"Critical symptom detected: {keyword}")
                return True

        return False

    def get_routing_explanation(self, routing_result: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of routing decision.

        Useful for debugging and understanding why a message was routed a certain way.
        """
        agent = routing_result.get("agent_to_call", "unknown").replace("_agent", "")
        confidence = routing_result.get("confidence", 0.5)
        reason = routing_result.get("reason", "Unknown")

        return (
            f"Route: {agent.upper()} "
            f"(confidence: {confidence:.0%}) - {reason}"
        )


def get_orchestrator_agent() -> OrchestratorAgent:
    """Get or create orchestrator agent instance."""
    return OrchestratorAgent()
