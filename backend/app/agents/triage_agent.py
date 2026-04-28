"""Triage Agent - urgency assessment & emergency escalation.

This agent:
1. Analyzes patient message for urgency indicators
2. Scores severity on 1-10 scale
3. Determines escalation path (self-care, urgent care, ER)
4. Provides immediate action recommendations
5. Routes critical cases to emergency

Follows clean architecture: delegates to EuriService for LLM analysis.
"""

import logging
from typing import Optional, Dict, Any
from app.services.euri_service import get_euri_service

logger = logging.getLogger(__name__)


class TriageAgent:
    """Emergency assessment and patient escalation."""

    def __init__(self):
        """Initialize agent with Euri service."""
        self.euri = get_euri_service()
        self.agent_name = "triage"

    def assess_urgency(
        self,
        patient_message: str,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assess patient urgency and recommend escalation path.

        Flow:
        1. Analyze message with Euri for urgency cues
        2. Score severity (1-10)
        3. Determine escalation level (self-care, urgent, critical)
        4. Provide immediate recommendations
        5. Return structured urgency assessment

        Args:
            patient_message: Patient's message describing symptoms/concern
            patient_info: Optional patient metadata (age, allergies, meds)

        Returns:
            {
                "urgency_level": "critical|urgent|moderate|self-care",
                "severity_score": 8,  # 1-10
                "requires_escalation": True,
                "escalation_path": "ER" or "Urgent Care" or "Doctor Visit" or "Self-Care",
                "immediate_action": "Call 911 or go to nearest emergency room immediately",
                "reasoning": "Chest pain with shortness of breath indicates cardiac risk",
                "warning_signs": ["Severe chest pain", "Difficulty breathing"],
                "next_steps": ["Seek immediate medical attention", "Do not drive yourself"],
                "confidence_score": 0.98,
                "agent_used": "triage",
                "response": "Full formatted response for patient",
                "disclaimer": "This assessment is not a medical diagnosis..."
            }
        """
        try:
            logger.info(f"Triage agent assessing: {patient_message[:100]}...")

            # Step 1: Call Euri to analyze urgency
            triage_result = self.euri.generate_triage_assessment(
                patient_message=patient_message,
                patient_info=patient_info,
            )
            logger.debug("Triage assessment generated")

            # Step 2: Extract structured data
            urgency_level = triage_result.get("urgency_level", "moderate")
            severity_score = triage_result.get("severity_score", 5)
            escalation_path = triage_result.get("escalation_path", "Doctor Visit")
            warning_signs = triage_result.get("warning_signs", [])
            immediate_action = triage_result.get("immediate_action", "")

            # Step 3: Determine if escalation is needed
            requires_escalation = urgency_level in ["critical", "urgent"]

            # Step 4: Build patient-facing response
            response_text = self._build_patient_response(
                urgency_level=urgency_level,
                severity_score=severity_score,
                escalation_path=escalation_path,
                immediate_action=immediate_action,
                warning_signs=warning_signs,
            )

            print(
                f"DEBUG [TRIAGE_AGENT]: Assessed urgency={urgency_level}, "
                f"severity={severity_score}/10, escalation={escalation_path}"
            )

            return {
                "urgency_level": urgency_level,
                "severity_score": severity_score,
                "requires_escalation": requires_escalation,
                "escalation_path": escalation_path,
                "immediate_action": immediate_action,
                "reasoning": triage_result.get("reasoning", ""),
                "warning_signs": warning_signs,
                "next_steps": triage_result.get("next_steps", []),
                "confidence_score": triage_result.get("confidence_score", 0.9),
                "agent_used": self.agent_name,
                "response": response_text,
                "disclaimer": (
                    "⚠️  IMPORTANT DISCLAIMER: This assessment is not a medical diagnosis. "
                    "If you experience chest pain, difficulty breathing, loss of consciousness, "
                    "or severe symptoms, seek immediate medical attention by calling 911 or "
                    "going to the nearest emergency room."
                ),
            }

        except Exception as e:
            logger.error(f"Triage assessment failed: {e}")
            # Fallback: when in doubt, escalate
            return {
                "urgency_level": "urgent",
                "severity_score": 7,
                "requires_escalation": True,
                "escalation_path": "Urgent Care",
                "immediate_action": (
                    "We were unable to fully assess your condition. "
                    "Please contact a healthcare provider or visit an urgent care facility."
                ),
                "response": (
                    "I was unable to process your message completely. "
                    "For your safety, please seek medical attention from a healthcare provider. "
                    "Call 911 if you experience chest pain, difficulty breathing, or other severe symptoms."
                ),
                "confidence_score": 0.0,
                "agent_used": self.agent_name,
                "error": str(e),
                "disclaimer": (
                    "⚠️  IMPORTANT DISCLAIMER: This assessment is not a medical diagnosis. "
                    "Please seek immediate medical attention if you experience severe symptoms."
                ),
            }

    def assess_vital_signs(
        self,
        vitals: Dict[str, Any],
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assess whether vital signs indicate urgency.

        Args:
            vitals: Dict with heart_rate, blood_pressure, temperature, oxygen_saturation
            patient_info: Patient metadata (age, medical_history, medications)

        Returns:
            {
                "vital_signs_normal": True/False,
                "abnormal_vitals": ["High heart rate (120 bpm)"],
                "urgency_level": "critical|urgent|moderate|normal",
                "recommendations": "...",
                "response": "..."
            }
        """
        try:
            logger.info(f"Triage agent assessing vitals")

            # Build vital signs assessment message
            vitals_summary = self._format_vitals_summary(vitals, patient_info)
            logger.debug(f"Vitals summary: {vitals_summary}")

            # Call Euri to analyze vitals
            assessment = self.euri.generate_triage_assessment(
                patient_message=f"Patient vital signs: {vitals_summary}",
                patient_info=patient_info,
                assessment_type="vitals",
            )

            abnormal_vitals = self._identify_abnormal_vitals(vitals, patient_info)

            return {
                "vital_signs_normal": len(abnormal_vitals) == 0,
                "abnormal_vitals": abnormal_vitals,
                "urgency_level": assessment.get("urgency_level", "moderate"),
                "severity_score": assessment.get("severity_score", 5),
                "recommendations": assessment.get("immediate_action", "Monitor closely"),
                "response": assessment.get("reasoning", "Vital signs reviewed"),
                "confidence_score": assessment.get("confidence_score", 0.85),
                "agent_used": self.agent_name,
            }

        except Exception as e:
            logger.error(f"Vital sign assessment failed: {e}")
            return {
                "vital_signs_normal": False,
                "abnormal_vitals": [],
                "urgency_level": "urgent",
                "recommendations": "Please contact a healthcare provider",
                "response": "Unable to assess vital signs",
                "error": str(e),
                "agent_used": self.agent_name,
            }

    def _build_patient_response(
        self,
        urgency_level: str,
        severity_score: int,
        escalation_path: str,
        immediate_action: str,
        warning_signs: list,
    ) -> str:
        """Build human-readable patient response based on triage assessment."""
        if urgency_level == "critical":
            return (
                f"🚨 **CRITICAL - SEEK IMMEDIATE MEDICAL ATTENTION** 🚨\n\n"
                f"Your symptoms require emergency care.\n\n"
                f"**IMMEDIATE ACTION:**\n"
                f"{immediate_action}\n\n"
                f"**ESCALATION PATH:** {escalation_path}\n\n"
                f"**WARNING SIGNS YOU REPORTED:**\n"
                f"{chr(10).join(f'- {sign}' for sign in warning_signs)}\n\n"
                f"**Do not delay - seek emergency care now.**"
            )
        elif urgency_level == "urgent":
            return (
                f"⚠️  **URGENT - Seek prompt medical attention**\n\n"
                f"Your symptoms need to be evaluated by a healthcare provider.\n\n"
                f"**ACTION RECOMMENDED:**\n"
                f"{immediate_action}\n\n"
                f"**ESCALATION PATH:** {escalation_path}\n\n"
                f"**SYMPTOMS OF CONCERN:**\n"
                f"{chr(10).join(f'- {sign}' for sign in warning_signs)}\n\n"
                f"**Contact your doctor or visit an urgent care facility soon.**"
            )
        elif urgency_level == "moderate":
            return (
                f"ℹ️  **Schedule a doctor's appointment**\n\n"
                f"Your symptoms should be evaluated by a healthcare provider.\n\n"
                f"**RECOMMENDED ACTION:**\n"
                f"{immediate_action}\n\n"
                f"**ESCALATION PATH:** {escalation_path}\n\n"
                f"**Contact your doctor to schedule an appointment.**\n"
                f"If symptoms worsen, seek urgent care."
            )
        else:  # self-care
            return (
                f"✅ **Self-care manageable**\n\n"
                f"Your symptoms may be managed with self-care measures.\n\n"
                f"**RECOMMENDATIONS:**\n"
                f"{immediate_action}\n\n"
                f"**ESCALATION PATH:** {escalation_path}\n\n"
                f"**If symptoms persist or worsen, contact your doctor.**"
            )

    def _format_vitals_summary(
        self,
        vitals: Dict[str, Any],
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Format vital signs into readable summary."""
        age = patient_info.get("age") if patient_info else None
        age_str = f"(age {age})" if age else ""

        summary = f"Patient {age_str}:\n"

        if vitals.get("heart_rate"):
            summary += f"- Heart Rate: {vitals['heart_rate']} bpm\n"
        if vitals.get("blood_pressure_systolic"):
            sys = vitals["blood_pressure_systolic"]
            dia = vitals.get("blood_pressure_diastolic", "?")
            summary += f"- Blood Pressure: {sys}/{dia} mmHg\n"
        if vitals.get("temperature"):
            summary += f"- Temperature: {vitals['temperature']} °C\n"
        if vitals.get("oxygen_saturation"):
            summary += f"- Oxygen Saturation: {vitals['oxygen_saturation']}%\n"
        if vitals.get("respiratory_rate"):
            summary += f"- Respiratory Rate: {vitals['respiratory_rate']} breaths/min\n"

        return summary

    def _identify_abnormal_vitals(
        self,
        vitals: Dict[str, Any],
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> list:
        """Identify which vital signs are outside normal range."""
        abnormal = []
        age = patient_info.get("age") if patient_info else None

        # Heart rate: 60-100 bpm (normal)
        if vitals.get("heart_rate"):
            hr = vitals["heart_rate"]
            if hr < 60:
                abnormal.append(f"Low heart rate ({hr} bpm)")
            elif hr > 100:
                abnormal.append(f"Elevated heart rate ({hr} bpm)")

        # Blood pressure: <120/80 (normal)
        if vitals.get("blood_pressure_systolic"):
            sys = vitals["blood_pressure_systolic"]
            dia = vitals.get("blood_pressure_diastolic", 0)
            if sys >= 140 or dia >= 90:
                abnormal.append(f"High blood pressure ({sys}/{dia} mmHg)")
            elif sys < 90 or dia < 60:
                abnormal.append(f"Low blood pressure ({sys}/{dia} mmHg)")

        # Temperature: 36.5-37.5°C (normal)
        if vitals.get("temperature"):
            temp = vitals["temperature"]
            if temp < 36.5:
                abnormal.append(f"Low temperature ({temp}°C)")
            elif temp > 37.5:
                abnormal.append(f"Elevated temperature/fever ({temp}°C)")

        # Oxygen saturation: >95% (normal)
        if vitals.get("oxygen_saturation"):
            spo2 = vitals["oxygen_saturation"]
            if spo2 < 95:
                abnormal.append(f"Low oxygen saturation ({spo2}%)")

        # Respiratory rate: 12-20 breaths/min (normal)
        if vitals.get("respiratory_rate"):
            rr = vitals["respiratory_rate"]
            if rr < 12:
                abnormal.append(f"Low respiratory rate ({rr} breaths/min)")
            elif rr > 20:
                abnormal.append(f"Elevated respiratory rate ({rr} breaths/min)")

        return abnormal


def get_triage_agent() -> TriageAgent:
    """Get or create triage agent instance."""
    return TriageAgent()
