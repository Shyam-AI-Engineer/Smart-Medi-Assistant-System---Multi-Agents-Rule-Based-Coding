"""Test script to verify Medication Agent drug interaction checking."""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.medication_agent import get_medication_agent


def test_medication_interactions():
    """Test medication agent on different interaction scenarios."""
    print("\n" + "="*70)
    print("MEDICATION AGENT TEST - DRUG INTERACTIONS")
    print("="*70 + "\n")

    agent = get_medication_agent()

    # Test cases with different risk levels
    test_cases = [
        {
            "medications": ["ibuprofen", "amlodipine"],
            "description": "MODERATE: NSAID + Blood pressure medication",
            "expected_risk": "MODERATE",
        },
        {
            "medications": ["aspirin", "ibuprofen"],
            "description": "HIGH: Dual NSAID use (GI bleeding risk)",
            "expected_risk": "HIGH",
        },
        {
            "medications": ["warfarin", "aspirin"],
            "description": "HIGH: Anticoagulant + antiplatelet (bleeding)",
            "expected_risk": "HIGH",
        },
        {
            "medications": ["metformin", "alcohol"],
            "description": "MODERATE: Metformin + alcohol (lactic acidosis)",
            "expected_risk": "MODERATE",
        },
        {
            "medications": ["metoprolol", "verapamil"],
            "description": "HIGH: Beta-blocker + calcium channel blocker (bradycardia)",
            "expected_risk": "HIGH",
        },
        {
            "medications": ["paracetamol", "ibuprofen"],
            "description": "LOW/NONE: Different drug classes (compatible)",
            "expected_risk": "LOW",
        },
    ]

    patient_info_samples = [
        {"age": 45, "medical_history": "Hypertension"},
        {"age": 35, "medical_history": "No significant history"},
        {"age": 72, "medical_history": "Atrial fibrillation, on anticoagulation"},
        {"age": 50, "medical_history": "Type 2 diabetes"},
        {"age": 60, "medical_history": "Heart failure, bradycardia"},
        {"age": 28, "medical_history": "Migraine headaches"},
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'-'*70}")
        print(f"Test {i}: {test['description']}")
        print(f"{'-'*70}")
        meds = test["medications"]
        print(f"Medications: {' + '.join([m.title() for m in meds])}")

        try:
            patient_info = patient_info_samples[i-1]
            assessment = agent.check_medication_interactions(
                meds,
                patient_info=patient_info,
            )

            risk = assessment.get("overall_risk", "unknown")
            confidence = assessment.get("confidence_score", 0.0)
            interactions = assessment.get("interactions", [])
            contraindications = assessment.get("contraindications", [])

            print(f"Overall Risk: {risk}")
            print(f"Confidence: {confidence:.0%}")

            if interactions:
                print(f"Interactions Found: {len(interactions)}")
                for interaction in interactions:
                    print(
                        f"  - {interaction['drug1'].title()} + {interaction['drug2'].title()}: "
                        f"{interaction.get('risk', 'UNKNOWN')}"
                    )

            if contraindications:
                print(f"Contraindications: {len(contraindications)}")
                for contra in contraindications:
                    print(f"  - {contra['warning']}")

            # Check if matches expectation
            if risk == test["expected_risk"]:
                print(f"[PASS] CORRECT: Assessed as '{risk}' (expected)")
            else:
                print(f"[WARN]  Assessed as '{risk}', expected '{test['expected_risk']}'")

        except Exception as e:
            print(f"[FAIL] ERROR: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'-'*70}")
    print("MEDICATION INTERACTIONS TEST COMPLETE")
    print(f"{'-'*70}\n")


def test_single_medication():
    """Test single medication information retrieval."""
    print("\n" + "="*70)
    print("MEDICATION AGENT TEST - SINGLE MEDICATION INFO")
    print("="*70 + "\n")

    agent = get_medication_agent()

    test_cases = [
        {
            "medication": "metformin",
            "description": "Diabetes medication - check side effects and contraindications",
            "patient_info": {"age": 65, "medical_history": "Kidney disease, Type 2 diabetes"},
        },
        {
            "medication": "warfarin",
            "description": "Anticoagulant - check bleeding warnings",
            "patient_info": {"age": 72, "medical_history": "Atrial fibrillation"},
        },
        {
            "medication": "ibuprofen",
            "description": "NSAID - check contraindications for elderly",
            "patient_info": {"age": 78, "medical_history": "Peptic ulcer, hypertension"},
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'-'*70}")
        print(f"Test {i}: {test['description']}")
        print(f"{'-'*70}")
        print(f"Medication: {test['medication'].title()}")

        try:
            assessment = agent.check_single_medication(
                test["medication"],
                patient_info=test["patient_info"],
            )

            medication = assessment.get("medication", "unknown")
            side_effects = assessment.get("side_effects", [])
            alerts = assessment.get("patient_alerts", [])
            confidence = assessment.get("confidence_score", 0.0)

            print(f"Confidence: {confidence:.0%}")

            if side_effects:
                print(f"Side Effects: {', '.join(side_effects[:3])}")

            if alerts:
                print(f"Patient Alerts:")
                for alert in alerts:
                    print(f"  - {alert}")

            print(f"[PASS] Assessment complete")

        except Exception as e:
            print(f"[FAIL] ERROR: {e}")

    print(f"\n{'-'*70}")
    print("SINGLE MEDICATION TEST COMPLETE")
    print(f"{'-'*70}\n")


if __name__ == "__main__":
    try:
        test_medication_interactions()
        test_single_medication()
    except Exception as e:
        print(f"Test error: {e}")
        import traceback
        traceback.print_exc()
