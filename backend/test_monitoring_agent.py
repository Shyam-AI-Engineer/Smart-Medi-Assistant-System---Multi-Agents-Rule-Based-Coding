"""Test script to verify Monitoring Agent vital sign analysis."""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.monitoring_agent import get_monitoring_agent


def test_vital_analysis():
    """Test monitoring agent on different vital sign scenarios."""
    print("\n" + "="*70)
    print("MONITORING AGENT TEST - VITAL SIGN ANALYSIS")
    print("="*70 + "\n")

    agent = get_monitoring_agent()

    # Test cases with different risk levels
    test_cases = [
        {
            "vitals": {
                "heart_rate": 72,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "oxygen_saturation": 98,
                "temperature": 37.0,
            },
            "description": "NORMAL: All vitals within healthy range",
            "expected_status": "NORMAL",
        },
        {
            "vitals": {
                "heart_rate": 105,
                "blood_pressure_systolic": 125,
                "blood_pressure_diastolic": 82,
                "oxygen_saturation": 97,
                "temperature": 37.2,
            },
            "description": "MODERATE: Slightly elevated heart rate",
            "expected_status": "MODERATE",
        },
        {
            "vitals": {
                "heart_rate": 145,
                "blood_pressure_systolic": 155,
                "blood_pressure_diastolic": 98,
                "oxygen_saturation": 96,
                "temperature": 38.5,
            },
            "description": "HIGH: Multiple elevated vitals + fever",
            "expected_status": "HIGH",
        },
        {
            "vitals": {
                "heart_rate": 45,
                "blood_pressure_systolic": 88,
                "blood_pressure_diastolic": 55,
                "oxygen_saturation": 88,
                "temperature": 34.5,
            },
            "description": "CRITICAL: Dangerously low vitals",
            "expected_status": "CRITICAL",
        },
        {
            "vitals": {
                "heart_rate": 55,
                "blood_pressure_systolic": 110,
                "blood_pressure_diastolic": 75,
                "oxygen_saturation": 89,
                "temperature": 37.0,
            },
            "description": "HIGH: Low oxygen saturation (hypoxia)",
            "expected_status": "HIGH",
        },
        {
            "vitals": {
                "heart_rate": 92,
                "blood_pressure_systolic": 128,
                "blood_pressure_diastolic": 85,
                "oxygen_saturation": 95,
                "temperature": 39.2,
            },
            "description": "HIGH: High fever with normal other vitals",
            "expected_status": "HIGH",
        },
    ]

    patient_info_samples = [
        {"age": 35, "medical_history": "No significant history"},
        {"age": 45, "medical_history": "Hypertension"},
        {"age": 60, "medical_history": "Heart disease, diabetes"},
        {"age": 78, "medical_history": "Elderly, multiple comorbidities"},
        {"age": 50, "medical_history": "Asthma"},
        {"age": 40, "medical_history": "No significant history"},
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'-'*70}")
        print(f"Test {i}: {test['description']}")
        print(f"{'-'*70}")

        try:
            patient_info = patient_info_samples[i-1]
            assessment = agent.analyze_vitals(
                test["vitals"],
                patient_info=patient_info,
            )

            status = assessment.get("overall_status", "unknown")
            confidence = assessment.get("confidence_score", 0.0)
            vital_count = len(assessment.get("vital_analyses", []))
            escalate = assessment.get("should_escalate_to_triage", False)

            print(f"Overall Status: {status}")
            print(f"Confidence: {confidence:.0%}")
            print(f"Vitals Analyzed: {vital_count}")
            print(f"Escalate to Triage: {escalate}")

            # Show vital details
            for vital in assessment.get("vital_analyses", [])[:3]:
                print(
                    f"  - {vital['vital_type']}: {vital['value']} {vital['unit']} "
                    f"({vital['status']})"
                )

            # Check if matches expectation
            if status == test["expected_status"]:
                print(f"[PASS] CORRECT: Assessed as '{status}' (expected)")
            else:
                print(
                    f"[WARN] Assessed as '{status}', "
                    f"expected '{test['expected_status']}'"
                )

            # Show recommendations
            recs = assessment.get("recommendations", [])
            if recs:
                print(f"Recommendations:")
                for rec in recs[:2]:
                    print(f"  - {rec}")

        except Exception as e:
            print(f"[FAIL] ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'-'*70}")
    print("MONITORING AGENT TEST COMPLETE")
    print(f"{'-'*70}\n")


def test_critical_escalation():
    """Test that critical vitals trigger escalation to triage."""
    print("\n" + "="*70)
    print("MONITORING AGENT TEST - CRITICAL ESCALATION")
    print("="*70 + "\n")

    agent = get_monitoring_agent()

    critical_test = {
        "heart_rate": 155,           # Way too high
        "blood_pressure_systolic": 190,  # Hypertensive crisis
        "blood_pressure_diastolic": 120,
        "oxygen_saturation": 82,     # Severe hypoxia
        "temperature": 40.5,         # Dangerous fever
    }

    print("Testing CRITICAL vitals that should trigger triage escalation...")
    print(f"Vitals: {critical_test}")

    try:
        assessment = agent.analyze_vitals(critical_test)

        status = assessment.get("overall_status")
        escalate = assessment.get("should_escalate_to_triage")
        severity = assessment.get("severity_level")

        print(f"\nStatus: {status}")
        print(f"Severity Level: {severity}")
        print(f"Escalate to Triage: {escalate}")

        if escalate and status == "CRITICAL":
            print("[PASS] CORRECT: Critical vitals triggered escalation")
        else:
            print("[FAIL] WRONG: Should have escalated to triage")

        # Show assessment
        assessment_text = assessment.get("overall_assessment", "")
        print(f"\nAssessment: {assessment_text[:150]}...")

    except Exception as e:
        print(f"[FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n{'-'*70}")
    print("CRITICAL ESCALATION TEST COMPLETE")
    print(f"{'-'*70}\n")


if __name__ == "__main__":
    try:
        test_vital_analysis()
        test_critical_escalation()
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
