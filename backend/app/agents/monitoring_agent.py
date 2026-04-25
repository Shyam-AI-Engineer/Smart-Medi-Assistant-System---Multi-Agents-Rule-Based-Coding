"""Monitoring Agent - analyzes vital signs and detects anomalies."""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.euri_service import get_euri_service
from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Vital sign normal ranges and thresholds
VITAL_THRESHOLDS = {
    "heart_rate": {
        "critical_low": 40,      # bpm
        "low": 60,
        "normal_min": 60,
        "normal_max": 100,
        "high": 100,
        "critical_high": 140,
        "unit": "bpm",
    },
    "blood_pressure_systolic": {
        "critical_low": 90,      # mmHg
        "low": 100,
        "normal_min": 100,
        "normal_max": 120,
        "high": 140,             # Stage 1 hypertension
        "critical_high": 180,
        "unit": "mmHg",
    },
    "blood_pressure_diastolic": {
        "critical_low": 50,      # mmHg
        "low": 60,
        "normal_min": 60,
        "normal_max": 80,
        "high": 90,              # Stage 1 hypertension
        "critical_high": 120,
        "unit": "mmHg",
    },
    "oxygen_saturation": {
        "critical_low": 85,      # percent
        "low": 90,
        "normal_min": 95,
        "normal_max": 100,
        "high": 100,
        "critical_high": 100,
        "unit": "%",
    },
    "temperature": {
        "critical_low": 34.0,    # Celsius
        "low": 36.0,
        "normal_min": 36.5,
        "normal_max": 37.5,
        "high": 38.0,            # Fever
        "critical_high": 40.0,
        "unit": "°C",
    },
    "respiratory_rate": {
        "critical_low": 8,       # breaths/min
        "low": 12,
        "normal_min": 12,
        "normal_max": 20,
        "high": 24,
        "critical_high": 30,
        "unit": "breaths/min",
    },
}

# Severity levels
SEVERITY_LEVELS = {
    "CRITICAL": {
        "level": 4,
        "emoji": "🚨",
        "action": "SEEK IMMEDIATE MEDICAL ATTENTION",
    },
    "HIGH": {
        "level": 3,
        "emoji": "⚠️",
        "action": "Consult doctor soon",
    },
    "MODERATE": {
        "level": 2,
        "emoji": "⚡",
        "action": "Monitor and follow up with doctor",
    },
    "NORMAL": {
        "level": 1,
        "emoji": "✅",
        "action": "Continue regular monitoring",
    },
}


class MonitoringAgent(BaseAgent):
    """Analyzes vital signs and detects anomalies."""

    def __init__(self):
        """Initialize monitoring agent with Euri service."""
        super().__init__("monitoring")
        self.euri = get_euri_service()
        logger.info("MonitoringAgent initialized")

    def process(self, **kwargs) -> Dict[str, Any]:
        """
        Process vitals analysis request (implements BaseAgent.process).

        Expected kwargs:
            - vitals: Dict[str, float] - vital measurements
            - patient_info: Optional[Dict] - patient context

        Returns structured response with analysis and recommendations.
        """
        vitals = kwargs.get("vitals", {})
        patient_info = kwargs.get("patient_info")

        if not vitals:
            return {
                "response": "No vital signs provided for analysis.",
                "agent_used": "monitoring",
                "confidence_score": 0.0,
                "tokens_used": 0,
                "error": True,
            }

        return self.analyze_vitals(vitals, patient_info)

    def analyze_vitals(
        self,
        vitals: Dict[str, float],
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze vital signs and detect abnormalities.

        Args:
            vitals: Dict of vital measurements
                {
                    "heart_rate": 120,
                    "blood_pressure_systolic": 145,
                    "blood_pressure_diastolic": 92,
                    "oxygen_saturation": 96,
                    "temperature": 38.5,
                    "respiratory_rate": 22
                }
            patient_info: Patient context (age, conditions, medications)

        Returns:
            {
                "overall_status": "CRITICAL|HIGH|MODERATE|NORMAL",
                "severity_level": 4,
                "vital_analyses": [
                    {
                        "vital_type": "heart_rate",
                        "value": 120,
                        "unit": "bpm",
                        "status": "HIGH",
                        "severity": "MODERATE",
                        "explanation": "Elevated heart rate may indicate...",
                        "recommendation": "Monitor closely",
                        "confidence": 0.93
                    }
                ],
                "critical_findings": ["High heart rate", "Elevated temperature"],
                "overall_assessment": "Patient has elevated vitals...",
                "recommendations": ["Monitor heart rate", "Check temperature regularly"],
                "should_escalate_to_triage": True,
                "confidence_score": 0.92,
                "agent_used": "monitoring",
                "tokens_used": 450,
                "response": "Patient-friendly formatted message",
                "disclaimer": "..."
            }
        """
        logger.info(f"Analyzing vitals: {list(vitals.keys())}")

        try:
            # Step 1: Analyze each vital sign
            vital_analyses = []
            critical_findings = []
            max_severity = "NORMAL"

            for vital_type, value in vitals.items():
                if vital_type not in VITAL_THRESHOLDS:
                    logger.warning(f"Unknown vital type: {vital_type}")
                    continue

                analysis = self._analyze_single_vital(vital_type, value, patient_info)
                vital_analyses.append(analysis)

                # Track critical findings
                if analysis["severity"] in ["CRITICAL", "HIGH"]:
                    critical_findings.append(f"{vital_type}: {analysis['status']}")

                # Update max severity
                if self._compare_severity(analysis["severity"], max_severity) > 0:
                    max_severity = analysis["severity"]

            # Step 2: Determine overall status
            overall_status = max_severity

            # Step 3: Generate overall assessment
            overall_assessment = self._generate_overall_assessment(
                vital_analyses,
                critical_findings,
                patient_info
            )

            # Step 4: Generate recommendations
            recommendations = self._generate_recommendations(
                vital_analyses,
                overall_status,
                patient_info
            )

            # Step 5: Determine escalation
            should_escalate = overall_status in ["CRITICAL", "HIGH"]

            response = {
                "overall_status": overall_status,
                "severity_level": SEVERITY_LEVELS[overall_status]["level"],
                "vital_analyses": vital_analyses,
                "critical_findings": critical_findings,
                "overall_assessment": overall_assessment,
                "recommendations": recommendations,
                "should_escalate_to_triage": should_escalate,
                "confidence_score": 0.93,
                "agent_used": "monitoring",
                "tokens_used": 450,
                "timestamp": datetime.utcnow().isoformat(),
                "disclaimer": self.get_disclaimer(overall_status),
                "response": self._format_patient_response(
                    vital_analyses,
                    overall_assessment,
                    recommendations,
                    overall_status
                ),
            }

            self.log_decision(
                "vitals_analyzed",
                {"status": overall_status, "vital_count": len(vital_analyses)}
            )
            return response

        except Exception as e:
            logger.error(f"Vital analysis failed: {e}")
            self.log_error("analyze_vitals", e)
            return self._error_response("Unable to analyze vital signs")

    def _analyze_single_vital(
        self,
        vital_type: str,
        value: float,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze single vital sign."""
        thresholds = VITAL_THRESHOLDS[vital_type]

        # Determine status
        if value <= thresholds["critical_low"]:
            status = "CRITICAL_LOW"
            severity = "CRITICAL"
        elif value < thresholds["low"]:
            status = "LOW"
            severity = "HIGH"
        elif value >= thresholds["normal_min"] and value <= thresholds["normal_max"]:
            status = "NORMAL"
            severity = "NORMAL"
        elif value <= thresholds["high"]:
            status = "ELEVATED"
            severity = "MODERATE"
        elif value < thresholds["critical_high"]:
            status = "HIGH"
            severity = "HIGH"
        else:
            status = "CRITICAL_HIGH"
            severity = "CRITICAL"

        # Get LLM explanation
        explanation = self._get_vital_explanation(vital_type, value, status, severity)

        # Get recommendation
        recommendation = self._get_vital_recommendation(vital_type, severity, patient_info)

        return {
            "vital_type": vital_type,
            "value": value,
            "unit": thresholds["unit"],
            "status": status,
            "severity": severity,
            "normal_range": {
                "min": thresholds["normal_min"],
                "max": thresholds["normal_max"],
            },
            "explanation": explanation,
            "recommendation": recommendation,
            "confidence": 0.93,
        }

    def _get_vital_explanation(
        self,
        vital_type: str,
        value: float,
        status: str,
        severity: str,
    ) -> str:
        """Get LLM-based explanation for vital sign."""
        prompt = (
            f"{vital_type}: {value} ({status}). "
            f"Briefly explain what this means for health. Keep to 1-2 sentences."
        )

        try:
            response = self.euri.client.chat.completions.create(
                model=self.euri.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical assistant explaining vital signs to patients. Be clear and non-alarming.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=100,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Failed to get LLM explanation: {e}")
            return f"{vital_type} is {status.lower()} - consult doctor if concerned"

    def _get_vital_recommendation(
        self,
        vital_type: str,
        severity: str,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get recommendation for abnormal vital sign."""
        recommendations = {
            "CRITICAL": {
                "heart_rate": "SEEK IMMEDIATE MEDICAL ATTENTION - call 911",
                "blood_pressure_systolic": "SEEK IMMEDIATE MEDICAL ATTENTION - call 911",
                "blood_pressure_diastolic": "SEEK IMMEDIATE MEDICAL ATTENTION - call 911",
                "oxygen_saturation": "SEEK IMMEDIATE MEDICAL ATTENTION - call 911",
                "temperature": "SEEK IMMEDIATE MEDICAL ATTENTION if accompanied by severe symptoms",
                "respiratory_rate": "SEEK IMMEDIATE MEDICAL ATTENTION - call 911",
            },
            "HIGH": {
                "heart_rate": "Contact doctor immediately - avoid strenuous activity",
                "blood_pressure_systolic": "Contact doctor immediately",
                "blood_pressure_diastolic": "Contact doctor immediately",
                "oxygen_saturation": "Contact doctor immediately - use oxygen if available",
                "temperature": "Contact doctor - monitor for worsening symptoms",
                "respiratory_rate": "Contact doctor immediately",
            },
            "MODERATE": {
                "heart_rate": "Monitor and report to doctor at next visit",
                "blood_pressure_systolic": "Monitor and report to doctor at next visit",
                "blood_pressure_diastolic": "Monitor and report to doctor at next visit",
                "oxygen_saturation": "Monitor closely - report to doctor",
                "temperature": "Monitor - increase fluids, use fever-reducing medication if needed",
                "respiratory_rate": "Monitor and report to doctor if persists",
            },
            "NORMAL": {
                "heart_rate": "Continue regular monitoring",
                "blood_pressure_systolic": "Continue regular monitoring",
                "blood_pressure_diastolic": "Continue regular monitoring",
                "oxygen_saturation": "Continue regular monitoring",
                "temperature": "Continue normal activities",
                "respiratory_rate": "Continue regular monitoring",
            },
        }

        return recommendations.get(severity, {}).get(vital_type, "Follow up with healthcare provider")

    def _generate_overall_assessment(
        self,
        vital_analyses: List[Dict[str, Any]],
        critical_findings: List[str],
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate overall assessment combining multiple vitals."""
        try:
            findings_text = ", ".join(critical_findings) if critical_findings else "No critical findings"

            prompt = (
                f"Patient vital signs: {findings_text}. "
                f"Provide brief overall health assessment (2-3 sentences). "
                f"Focus on safety and next steps."
            )

            response = self.euri.client.chat.completions.create(
                model=self.euri.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical triage assistant. Assess vital sign clusters for health status.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=150,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Failed to generate overall assessment: {e}")
            return "Patient vital signs require monitoring. Consult healthcare provider for complete evaluation."

    def _generate_recommendations(
        self,
        vital_analyses: List[Dict[str, Any]],
        overall_status: str,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Generate action recommendations."""
        recommendations = []

        # Add severity-based recommendations
        if overall_status == "CRITICAL":
            recommendations.append("Seek immediate medical attention or call 911")
        elif overall_status == "HIGH":
            recommendations.append("Contact healthcare provider immediately")
        elif overall_status == "MODERATE":
            recommendations.append("Schedule doctor appointment soon")

        # Add vital-specific recommendations
        abnormal_vitals = [v for v in vital_analyses if v["severity"] != "NORMAL"]
        for vital in abnormal_vitals[:3]:  # Top 3 abnormal vitals
            recommendations.append(f"Monitor {vital['vital_type']}")

        # Add patient-specific recommendations
        if patient_info:
            age = patient_info.get("age")
            if age and age > 65:
                recommendations.append("Ensure adequate rest and hydration")

        return recommendations[:5]  # Limit to 5 recommendations

    def _format_patient_response(
        self,
        vital_analyses: List[Dict[str, Any]],
        overall_assessment: str,
        recommendations: List[str],
        overall_status: str,
    ) -> str:
        """Format response for patient display."""
        lines = []

        # Header
        severity = SEVERITY_LEVELS.get(overall_status, {})
        lines.append(f"{severity.get('emoji', '⚠️')} **VITAL SIGNS ANALYSIS**\n")
        lines.append(f"Overall Status: **{overall_status}**\n")

        # Individual vital analyses
        lines.append("**Your Vital Signs:**")
        for vital in vital_analyses:
            lines.append(
                f"- {vital['vital_type'].replace('_', ' ').title()}: "
                f"{vital['value']} {vital['unit']} ({vital['status']})"
            )
        lines.append("")

        # Assessment
        lines.append("**Assessment:**")
        lines.append(overall_assessment)
        lines.append("")

        # Recommendations
        lines.append("**Recommended Actions:**")
        for rec in recommendations:
            lines.append(f"- {rec}")
        lines.append("")

        # Action based on severity
        action = severity.get("action", "Consult healthcare provider")
        lines.append(f"**Next Step:** {action}")
        lines.append("")

        # Disclaimer
        lines.append(self.get_disclaimer(overall_status))

        return "\n".join(lines)

    def _compare_severity(self, sev1: str, sev2: str) -> int:
        """Compare two severities. Returns 1 if sev1 > sev2, -1 if <, 0 if equal."""
        level_order = ["NORMAL", "MODERATE", "HIGH", "CRITICAL"]
        try:
            lev1 = level_order.index(sev1)
            lev2 = level_order.index(sev2)
            return 1 if lev1 > lev2 else (-1 if lev1 < lev2 else 0)
        except ValueError:
            return 0

    def _error_response(self, message: str) -> Dict[str, Any]:
        """Return error response."""
        return {
            "overall_status": "MODERATE",
            "severity_level": 2,
            "vital_analyses": [],
            "critical_findings": [],
            "overall_assessment": message,
            "recommendations": ["Consult healthcare provider"],
            "should_escalate_to_triage": False,
            "confidence_score": 0.0,
            "agent_used": "monitoring",
            "tokens_used": 0,
            "error": True,
            "disclaimer": self.get_disclaimer("MODERATE"),
            "response": message,
        }


# Singleton instance
_monitoring_agent: Optional[MonitoringAgent] = None


def get_monitoring_agent() -> MonitoringAgent:
    """Get or create monitoring agent instance."""
    global _monitoring_agent
    if _monitoring_agent is None:
        _monitoring_agent = MonitoringAgent()
    return _monitoring_agent
