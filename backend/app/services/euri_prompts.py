"""Pure prompt-building functions for the Euri LLM service."""
from typing import Any, Dict, Optional


def build_medical_system_prompt(patient_info: Optional[Dict[str, Any]] = None) -> str:
    prompt = (
        "You are a medical AI assistant providing health information to patients.\n\n"
        "CRITICAL RULES:\n"
        "1. Answer ONLY from the retrieved medical context provided below\n"
        "2. If the context is insufficient, SAY SO - do not hallucinate\n"
        "3. Always include a disclaimer: \"This is for informational purposes only, not medical advice\"\n"
        "4. Flag any critical symptoms that require immediate medical attention\n"
        "5. Recommend consulting a doctor for diagnosis or treatment decisions\n"
        "6. Be conservative and cautious in your recommendations\n"
        "7. Never prescribe medications or provide dosing advice\n"
        "8. Cite your sources (document title, section) when referencing specific information\n"
    )
    if patient_info:
        prompt += (
            f"\nPATIENT CONTEXT:\n"
            f"- Age: {patient_info.get('age', 'Unknown')}\n"
            f"- Allergies: {patient_info.get('allergies', 'None noted')}\n"
            f"- Current medications: {patient_info.get('medications', 'None noted')}\n"
            f"- Medical history: {patient_info.get('history', 'Not provided')}\n"
        )
        rv = patient_info.get("recent_vitals")
        if rv:
            prompt += (
                f"\nRECENT VITAL SIGNS (from {rv.get('timestamp', 'recent measurement')}):\n"
                f"- Heart Rate: {rv.get('heart_rate', 'Not recorded')} bpm\n"
                f"- Blood Pressure: {rv.get('blood_pressure_systolic', '?')}/{rv.get('blood_pressure_diastolic', '?')} mmHg\n"
                f"- Oxygen Saturation: {rv.get('oxygen_saturation', 'Not recorded')}%\n"
                f"- Temperature: {rv.get('temperature', 'Not recorded')} degrees C\n"
                f"- Respiratory Rate: {rv.get('respiratory_rate', 'Not recorded')} /min\n"
                f"- Weight: {rv.get('weight', 'Not recorded')} kg\n"
            )
    return prompt


def build_rag_message(
    patient_question: str,
    medical_context: str,
    patient_info: Optional[Dict[str, Any]] = None,
) -> str:
    return (
        f"Retrieved Medical Information:\n{'-' * 50}\n{medical_context}\n{'-' * 50}\n\n"
        f"Patient Question: {patient_question}\n\n"
        "Answer based ONLY on the retrieved context above."
    )


def build_triage_system_prompt(assessment_type: str = "general") -> str:
    common_scale = (
        "Urgency levels:\n"
        "- critical (9-10): Immediate life threat, call 108 (ambulance)\n"
        "- urgent (7-8): Needs evaluation within hours, go to ER/Urgent Care\n"
        "- moderate (4-6): Should see doctor today or within 24h\n"
        "- self-care (1-3): Manageable at home, monitor closely\n\n"
        "Respond with ONLY valid JSON:\n"
        "{\n"
        '    "urgency_level": "critical|urgent|moderate|self-care",\n'
        '    "severity_score": 1-10,\n'
        '    "escalation_path": "ER|Urgent Care|Doctor Visit|Self-Care",\n'
        '    "immediate_action": "...",\n'
        '    "warning_signs": ["..."],\n'
        '    "reasoning": "...",\n'
        '    "next_steps": ["..."],\n'
        '    "confidence_score": 0.0-1.0\n'
        "}"
    )
    if assessment_type == "vitals":
        return (
            "You are a medical triage agent specializing in vital sign assessment.\n\n"
            "CRITICAL RULES:\n"
            "1. Assess whether vital signs are normal or abnormal\n"
            "2. Score severity on 1-10 scale (10 = life-threatening)\n"
            "3. Determine escalation path based on severity\n"
            "4. Be CONSERVATIVE - when in doubt, escalate\n"
            "5. Consider patient age and medical history\n"
            "6. Identify specific warning signs\n\n"
            + common_scale
        )
    return (
        "You are a medical triage agent assessing patient urgency.\n\n"
        "CRITICAL RULES:\n"
        "1. Analyze symptoms for urgency indicators\n"
        "2. Look for red flags (chest pain, difficulty breathing, loss of consciousness, etc.)\n"
        "3. Score severity on 1-10 scale (10 = life-threatening)\n"
        "4. Determine appropriate escalation path\n"
        "5. Be CONSERVATIVE - when in doubt, escalate\n"
        "6. Consider patient age and medical history\n"
        "7. Identify specific warning signs that require emergency care\n\n"
        "Red flags that always escalate to ER:\n"
        "- Chest pain or pressure\n"
        "- Difficulty breathing or shortness of breath\n"
        "- Loss of consciousness or altered mental status\n"
        "- Severe bleeding\n"
        "- Severe allergic reaction\n"
        "- Signs of stroke (facial drooping, arm weakness, speech difficulty)\n"
        "- Severe abdominal pain\n"
        "- Poisoning or overdose\n\n"
        + common_scale
    )


def build_triage_message(
    patient_message: str,
    patient_info: Optional[Dict[str, Any]] = None,
    assessment_type: str = "general",
) -> str:
    msg = f"Patient presentation:\n{patient_message}"
    if patient_info:
        age = patient_info.get("age")
        history = patient_info.get("history") or patient_info.get("medical_history")
        meds = patient_info.get("medications") or patient_info.get("current_medications")
        allergies = patient_info.get("allergies")
        if any((age, history, meds, allergies)):
            msg += "\n\nPatient context:"
            if age:
                msg += f"\n- Age: {age}"
            if history:
                msg += f"\n- Medical history: {history}"
            if meds:
                msg += f"\n- Current medications: {meds}"
            if allergies:
                msg += f"\n- Allergies: {allergies}"
    suffix = "\n\nAssess these vital signs for abnormalities." if assessment_type == "vitals" \
        else "\n\nAssess the urgency of this patient's condition."
    return msg + suffix
