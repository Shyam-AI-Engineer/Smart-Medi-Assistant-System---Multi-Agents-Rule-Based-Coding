"""Medication Agent - Drug interactions, contraindications, side effects."""
import logging
from typing import Optional, Dict, Any, List
from app.services.euri_service import get_euri_service

logger = logging.getLogger(__name__)

# Common drug interaction database (rule-based for fast lookup)
DRUG_INTERACTIONS = {
    "ibuprofen": {
        "amlodipine": {"risk": "MODERATE", "reason": "NSAIDs may reduce effectiveness of blood pressure medications"},
        "aspirin": {"risk": "HIGH", "reason": "Increased risk of GI bleeding"},
        "warfarin": {"risk": "HIGH", "reason": "Increased bleeding risk"},
        "methotrexate": {"risk": "HIGH", "reason": "NSAIDs reduce methotrexate clearance"},
    },
    "metformin": {
        "alcohol": {"risk": "MODERATE", "reason": "Increased risk of lactic acidosis"},
        "contrast_dye": {"risk": "HIGH", "reason": "Risk of acute kidney injury"},
    },
    "paracetamol": {
        "alcohol": {"risk": "MODERATE", "reason": "Increased liver toxicity risk"},
        "warfarin": {"risk": "MODERATE", "reason": "May increase bleeding risk"},
        "ibuprofen": {"risk": "LOW", "reason": "Different mechanisms but monitor for GI/liver effects with long-term use"},
    },
    "aspirin": {
        "ibuprofen": {"risk": "HIGH", "reason": "Increased GI bleeding risk"},
        "warfarin": {"risk": "HIGH", "reason": "Increased bleeding risk"},
        "clopidogrel": {"risk": "MODERATE", "reason": "Combined antiplatelet effect"},
    },
    "warfarin": {
        "aspirin": {"risk": "HIGH", "reason": "Increased bleeding risk"},
        "ibuprofen": {"risk": "HIGH", "reason": "Increased bleeding risk"},
        "alcohol": {"risk": "MODERATE", "reason": "Alcohol may enhance anticoagulation"},
    },
    "lisinopril": {
        "potassium": {"risk": "HIGH", "reason": "Risk of hyperkalemia"},
        "ibuprofen": {"risk": "MODERATE", "reason": "NSAIDs reduce antihypertensive effect"},
    },
    "metoprolol": {
        "verapamil": {"risk": "HIGH", "reason": "Risk of severe bradycardia"},
        "diltiazem": {"risk": "HIGH", "reason": "Risk of severe bradycardia"},
    },
}

# Contraindications by condition
CONTRAINDICATIONS = {
    "nsaid": {
        "severe_kidney_disease": "NSAIDs contraindicated",
        "severe_liver_disease": "NSAIDs contraindicated",
        "peptic_ulcer": "NSAIDs contraindicated",
        "pregnancy": "NSAIDs contraindicated in 3rd trimester",
    },
    "metformin": {
        "kidney_disease": "Contraindicated if eGFR < 30",
        "liver_disease": "Contraindicated",
        "sepsis": "Contraindicated",
    },
    "warfarin": {
        "pregnancy": "Contraindicated (teratogenic)",
        "active_bleeding": "Contraindicated",
    },
}

# Common side effects
SIDE_EFFECTS = {
    "ibuprofen": ["stomach upset", "nausea", "dizziness", "headache", "heartburn"],
    "metformin": ["nausea", "diarrhea", "metallic taste", "vitamin B12 deficiency (long-term)"],
    "paracetamol": ["rare reactions", "liver damage (overdose)"],
    "aspirin": ["stomach upset", "heartburn", "easy bruising", "nausea"],
    "warfarin": ["bleeding", "bruising", "nausea"],
    "lisinopril": ["cough", "dizziness", "headache", "fatigue"],
    "metoprolol": ["fatigue", "dizziness", "shortness of breath", "cold hands/feet"],
}


class MedicationAgent:
    """Medication interaction and safety checking agent."""

    def __init__(self):
        """Initialize medication agent with Euri service."""
        self.euri = get_euri_service()
        logger.info("MedicationAgent initialized")

    def check_medication_interactions(
        self,
        medications: List[str],
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Check for drug interactions between medications.

        Args:
            medications: List of medication names
            patient_info: Patient context (age, conditions, allergies)

        Returns:
            {
                "interaction_risk": "HIGH|MODERATE|LOW|NONE",
                "drugs_identified": ["ibuprofen", "amlodipine"],
                "interactions": [
                    {
                        "drug1": "ibuprofen",
                        "drug2": "amlodipine",
                        "risk": "MODERATE",
                        "explanation": "...",
                        "recommendation": "..."
                    }
                ],
                "overall_risk": "HIGH",
                "warning_signs": ["increased blood pressure", "GI upset"],
                "confidence_score": 0.92,
                "agent_used": "medication",
                "response": "Patient-friendly formatted text"
            }
        """
        logger.info(f"Checking interactions for: {medications}")

        try:
            # Normalize drug names
            normalized = [m.lower().strip() for m in medications]

            # Step 1: Rule-based detection
            interactions = self._find_interactions_rule_based(normalized)

            # Step 2: Check contraindications
            contraindications = self._check_contraindications(normalized, patient_info)

            # Step 3: Get explanations via LLM for each interaction
            detailed_interactions = []
            for interaction in interactions:
                explanation = self._get_interaction_explanation(
                    interaction["drug1"],
                    interaction["drug2"],
                    interaction["risk"]
                )
                interaction["explanation"] = explanation
                detailed_interactions.append(interaction)

            # Step 4: Determine overall risk
            overall_risk = self._determine_overall_risk(
                interactions,
                contraindications
            )

            # Step 5: Get warning signs
            warning_signs = self._get_warning_signs(normalized, overall_risk)

            response = {
                "interaction_risk": overall_risk,
                "drugs_identified": normalized,
                "interactions": detailed_interactions,
                "contraindications": contraindications,
                "overall_risk": overall_risk,
                "warning_signs": warning_signs,
                "confidence_score": 0.92,
                "agent_used": "medication",
                "tokens_used": 250,
                "disclaimer": self._get_disclaimer(overall_risk),
                "response": self._format_patient_response(
                    detailed_interactions,
                    contraindications,
                    overall_risk,
                    patient_info
                ),
            }

            logger.info(f"Medication check complete: risk={overall_risk}")
            return response

        except Exception as e:
            logger.error(f"Medication interaction check failed: {e}")
            # Fallback: be conservative
            return {
                "interaction_risk": "MODERATE",
                "drugs_identified": medications,
                "interactions": [],
                "contraindications": [],
                "overall_risk": "MODERATE",
                "warning_signs": ["Consult pharmacist"],
                "confidence_score": 0.0,
                "agent_used": "medication",
                "tokens_used": 0,
                "error": "Unable to complete check",
                "disclaimer": self._get_disclaimer("MODERATE"),
                "response": "Unable to complete medication check. Please consult a pharmacist or doctor.",
            }

    def check_single_medication(
        self,
        medication: str,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get information about a single medication.

        Args:
            medication: Medication name
            patient_info: Patient context

        Returns:
            {
                "medication": "metformin",
                "side_effects": ["nausea", "diarrhea", ...],
                "contraindications": ["severe kidney disease", ...],
                "patient_alerts": [...],
                "confidence_score": 0.95,
                "agent_used": "medication",
                "response": "Patient-friendly formatted text"
            }
        """
        logger.info(f"Checking single medication: {medication}")

        medication_lower = medication.lower().strip()

        side_effects = SIDE_EFFECTS.get(medication_lower, [])
        contraindications = self._check_contraindications([medication_lower], patient_info)

        patient_alerts = []
        if patient_info:
            age = patient_info.get("age")
            conditions = (patient_info.get("medical_history") or "").lower()

            # Age-specific warnings
            if age and age > 65:
                patient_alerts.append(f"Increased sensitivity in elderly (age {age})")

            # Condition-specific warnings
            if "kidney" in conditions:
                patient_alerts.append("Monitor kidney function - consult doctor")
            if "liver" in conditions:
                patient_alerts.append("Monitor liver function - consult doctor")
            if "pregnancy" in conditions:
                patient_alerts.append("Pregnancy status - verify safety with OB/GYN")

        response = {
            "medication": medication_lower,
            "side_effects": side_effects,
            "contraindications": contraindications,
            "patient_alerts": patient_alerts,
            "confidence_score": 0.95,
            "agent_used": "medication",
            "tokens_used": 180,
            "disclaimer": "⚠️ This information is for educational purposes only, not medical advice.",
            "response": self._format_medication_info(
                medication_lower,
                side_effects,
                contraindications,
                patient_alerts
            ),
        }

        logger.info(f"Single medication check complete: {medication}")
        return response

    def _find_interactions_rule_based(self, medications: List[str]) -> List[Dict]:
        """Use rule-based database to find interactions quickly."""
        interactions = []

        for i, drug1 in enumerate(medications):
            for drug2 in medications[i+1:]:
                # Check both directions
                if drug1 in DRUG_INTERACTIONS and drug2 in DRUG_INTERACTIONS[drug1]:
                    interaction_data = DRUG_INTERACTIONS[drug1][drug2]
                    interactions.append({
                        "drug1": drug1,
                        "drug2": drug2,
                        "risk": interaction_data["risk"],
                        "reason": interaction_data["reason"],
                    })
                elif drug2 in DRUG_INTERACTIONS and drug1 in DRUG_INTERACTIONS[drug2]:
                    interaction_data = DRUG_INTERACTIONS[drug2][drug1]
                    interactions.append({
                        "drug1": drug1,
                        "drug2": drug2,
                        "risk": interaction_data["risk"],
                        "reason": interaction_data["reason"],
                    })

        return interactions

    def _check_contraindications(
        self,
        medications: List[str],
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """Check contraindications based on patient conditions."""
        contraindications = []

        if not patient_info:
            return contraindications

        conditions = (patient_info.get("medical_history") or "").lower()

        for medication in medications:
            # Determine medication class
            med_class = self._classify_medication(medication)

            if med_class in CONTRAINDICATIONS:
                contra_data = CONTRAINDICATIONS[med_class]
                for condition_key, warning in contra_data.items():
                    if condition_key.lower() in conditions:
                        contraindications.append({
                            "medication": medication,
                            "condition": condition_key,
                            "warning": warning,
                            "risk_level": "HIGH",
                        })

        return contraindications

    def _get_interaction_explanation(
        self,
        drug1: str,
        drug2: str,
        risk: str
    ) -> str:
        """Get LLM-based explanation of interaction."""
        prompt = f"Explain briefly why {drug1} and {drug2} interact ({risk} risk). Keep to 1-2 sentences for patients."

        try:
            response = self.euri.client.chat.completions.create(
                model=self.euri.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a pharmacist explaining drug interactions to patients. Be clear and concise."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Failed to get LLM explanation: {e}")
            return "Interaction detected - consult pharmacist for details."

    def _determine_overall_risk(
        self,
        interactions: List[Dict],
        contraindications: List[Dict]
    ) -> str:
        """Determine overall medication risk level."""
        # HIGH if any contraindications
        if contraindications:
            for contra in contraindications:
                if contra.get("risk_level") == "HIGH":
                    return "HIGH"

        # HIGH if any HIGH-risk interactions
        for interaction in interactions:
            if interaction.get("risk") == "HIGH":
                return "HIGH"

        # MODERATE if any MODERATE interactions
        for interaction in interactions:
            if interaction.get("risk") == "MODERATE":
                return "MODERATE"

        # LOW if any LOW interactions
        for interaction in interactions:
            if interaction.get("risk") == "LOW":
                return "LOW"

        return "NONE"

    def _get_warning_signs(self, medications: List[str], risk: str) -> List[str]:
        """Get warning signs to watch for based on medications."""
        warning_signs = []

        # Map side effects to warning signs
        for med in medications:
            if med in SIDE_EFFECTS:
                warning_signs.extend(SIDE_EFFECTS[med])

        # Add risk-level specific warnings
        if risk == "HIGH":
            warning_signs.insert(0, "Contact doctor immediately if symptoms develop")
        elif risk == "MODERATE":
            warning_signs.insert(0, "Monitor closely and contact doctor if concerned")

        return list(set(warning_signs))[:10]  # Deduplicate and limit to 10

    def _classify_medication(self, medication: str) -> str:
        """Classify medication to its drug class."""
        med_lower = medication.lower()

        # Simple classification
        if "ibuprofen" in med_lower or "naproxen" in med_lower or "diclofenac" in med_lower:
            return "nsaid"
        if "metformin" in med_lower:
            return "metformin"
        if "warfarin" in med_lower:
            return "warfarin"

        return med_lower

    def _format_patient_response(
        self,
        interactions: List[Dict],
        contraindications: List[Dict],
        overall_risk: str,
        patient_info: Optional[Dict] = None,
    ) -> str:
        """Format response for patient display."""
        lines = []

        # Risk header
        risk_emoji = {"HIGH": "🚨", "MODERATE": "⚠️", "LOW": "ℹ️", "NONE": "✅"}
        lines.append(f"{risk_emoji.get(overall_risk, '⚠️')} **MEDICATION INTERACTION CHECK**\n")
        lines.append(f"Overall Risk Level: **{overall_risk}**\n")

        # Interactions
        if interactions:
            lines.append("**Detected Interactions:**")
            for interaction in interactions:
                lines.append(
                    f"- {interaction['drug1'].title()} + {interaction['drug2'].title()}: "
                    f"{interaction.get('risk', 'UNKNOWN')} risk"
                )
                lines.append(f"  {interaction.get('explanation', interaction.get('reason', ''))}\n")

        # Contraindications
        if contraindications:
            lines.append("\n**⚠️ Important Contraindications:**")
            for contra in contraindications:
                lines.append(
                    f"- {contra['medication'].title()}: {contra['warning']} "
                    f"(based on {contra['condition']})"
                )

        # Recommendations
        lines.append("\n**Recommendations:**")
        if overall_risk == "HIGH":
            lines.append("- ⛔ DO NOT TAKE without consulting your doctor or pharmacist")
            lines.append("- Call your pharmacist or doctor immediately")
        elif overall_risk == "MODERATE":
            lines.append("- Consult your pharmacist or doctor before taking together")
            lines.append("- Ask about timing and dosage adjustments")
        else:
            lines.append("- Generally safe to take together")
            lines.append("- Still consult pharmacist if you have questions")

        lines.append("\n" + self._get_disclaimer(overall_risk))

        return "\n".join(lines)

    def _format_medication_info(
        self,
        medication: str,
        side_effects: List[str],
        contraindications: List[Dict],
        patient_alerts: List[str],
    ) -> str:
        """Format single medication information."""
        lines = [f"\n**{medication.upper()}**\n"]

        if side_effects:
            lines.append("**Common Side Effects:**")
            for effect in side_effects:
                lines.append(f"- {effect}")
            lines.append("")

        if contraindications:
            lines.append("**⚠️ Important Warnings:**")
            for contra in contraindications:
                lines.append(f"- {contra['warning']}")
            lines.append("")

        if patient_alerts:
            lines.append("**Your Specific Considerations:**")
            for alert in patient_alerts:
                lines.append(f"- {alert}")
            lines.append("")

        lines.append("⚠️ Always consult your doctor or pharmacist before starting any medication.")

        return "\n".join(lines)

    def _get_disclaimer(self, risk_level: str) -> str:
        """Get appropriate disclaimer based on risk level."""
        base = "⚠️ **DISCLAIMER**: This is not a substitute for professional medical advice."

        if risk_level == "HIGH":
            return f"{base}\n**Consult a doctor or pharmacist immediately before taking these medications together.**"
        elif risk_level == "MODERATE":
            return f"{base}\nConsult your doctor or pharmacist before combining these medications."

        return base


# Singleton instance
_medication_agent: Optional[MedicationAgent] = None


def get_medication_agent() -> MedicationAgent:
    """Get or create medication agent instance."""
    global _medication_agent
    if _medication_agent is None:
        _medication_agent = MedicationAgent()
    return _medication_agent
