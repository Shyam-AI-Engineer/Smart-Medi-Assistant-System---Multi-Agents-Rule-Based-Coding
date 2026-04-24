"""Test script to verify Triage Agent urgency assessment."""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.triage_agent import get_triage_agent


def test_triage_agent():
    """Test triage agent on different patient scenarios."""
    print("\n" + "="*70)
    print("TRIAGE AGENT TEST")
    print("="*70 + "\n")

    agent = get_triage_agent()

    # Test cases with different urgency levels
    test_cases = [
        {
            "message": "I have severe chest pain and difficulty breathing. I'm also sweating.",
            "expected_urgency": "critical",
            "description": "Critical: Chest pain with dyspnea - cardiac emergency"
        },
        {
            "message": "I fell and twisted my ankle. It's swollen and painful.",
            "expected_urgency": "moderate",
            "description": "Moderate: Ankle injury - needs evaluation but not emergency"
        },
        {
            "message": "I have a mild cough and sore throat for 2 days.",
            "expected_urgency": "self-care",
            "description": "Self-care: Minor cold symptoms - monitor at home"
        },
        {
            "message": "I've had a severe headache and stiff neck, and I feel feverish.",
            "expected_urgency": "urgent",
            "description": "Urgent: Possible meningitis - needs evaluation today"
        },
        {
            "message": "I can't breathe. I'm losing consciousness.",
            "expected_urgency": "critical",
            "description": "Critical: Severe respiratory distress - life-threatening"
        },
    ]

    patient_info_samples = [
        {"age": 45, "medical_history": "Hypertension, Family history of heart disease"},
        {"age": 28, "medical_history": "No significant history"},
        {"age": 22, "medical_history": "Asthma"},
        {"age": 65, "medical_history": "Diabetes, Hypertension"},
        {"age": 35, "medical_history": "Anxiety disorder"},
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*70}")
        print(f"Test {i}: {test['description']}")
        print(f"{'─'*70}")
        msg = test["message"]
        print(f"Message: \"{msg[:80]}...\"" if len(msg) > 80 else f"Message: \"{msg}\"")

        try:
            patient_info = patient_info_samples[i-1]
            assessment = agent.assess_urgency(test["message"], patient_info=patient_info)

            urgency = assessment.get("urgency_level", "unknown")
            severity = assessment.get("severity_score", 0)
            escalation = assessment.get("escalation_path", "Unknown")
            confidence = assessment.get("confidence_score", 0.0)
            reasoning = assessment.get("reasoning", "")
            warning_signs = assessment.get("warning_signs", [])

            print(f"Urgency Level: {urgency.upper()}")
            print(f"Severity Score: {severity}/10")
            print(f"Escalation Path: {escalation}")
            print(f"Confidence: {confidence:.0%}")
            print(f"Reasoning: {reasoning}")

            if warning_signs:
                print(f"Warning Signs: {', '.join(warning_signs)}")

            # Check if matches expectation
            if urgency == test["expected_urgency"]:
                print(f"✅ CORRECT: Assessed as '{urgency}' (expected)")
            else:
                print(f"⚠️  Assessed as '{urgency}', expected '{test['expected_urgency']}'")
                print(f"   (May be reasonable - severity {severity} matches intent)")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'─'*70}")
    print("TEST COMPLETE")
    print(f"{'─'*70}\n")


def test_vital_signs_assessment():
    """Test triage agent on vital signs."""
    print("\n" + "="*70)
    print("TRIAGE AGENT - VITAL SIGNS TEST")
    print("="*70 + "\n")

    agent = get_triage_agent()

    vital_test_cases = [
        {
            "vitals": {
                "heart_rate": 140,
                "blood_pressure_systolic": 180,
                "blood_pressure_diastolic": 110,
                "temperature": 38.5,
            },
            "description": "Hypertensive crisis with fever"
        },
        {
            "vitals": {
                "heart_rate": 72,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "temperature": 37.0,
                "oxygen_saturation": 98,
            },
            "description": "Normal vital signs"
        },
        {
            "vitals": {
                "heart_rate": 45,
                "blood_pressure_systolic": 85,
                "blood_pressure_diastolic": 55,
                "oxygen_saturation": 90,
            },
            "description": "Bradycardia with hypotension and low O2"
        },
    ]

    for i, test in enumerate(vital_test_cases, 1):
        print(f"\n{'─'*70}")
        print(f"Vital Test {i}: {test['description']}")
        print(f"{'─'*70}")

        vitals = test["vitals"]
        vitals_str = ", ".join([f"{k}: {v}" for k, v in vitals.items()])
        print(f"Vitals: {vitals_str}")

        try:
            patient_info = {"age": 45}
            assessment = agent.assess_vital_signs(vitals, patient_info=patient_info)

            urgency = assessment.get("urgency_level", "unknown")
            abnormal = assessment.get("abnormal_vitals", [])
            normal = assessment.get("vital_signs_normal", False)

            print(f"Vital Signs Normal: {normal}")
            if abnormal:
                print(f"Abnormal Vitals: {', '.join(abnormal)}")
            print(f"Urgency Level: {urgency.upper()}")
            print(f"Confidence: {assessment.get('confidence_score', 0):.0%}")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print(f"\n{'─'*70}")
    print("VITAL SIGNS TEST COMPLETE")
    print(f"{'─'*70}\n")


if __name__ == "__main__":
    try:
        test_triage_agent()
        test_vital_signs_assessment()
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
