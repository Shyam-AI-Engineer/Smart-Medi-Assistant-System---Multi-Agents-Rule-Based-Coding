"""Test script to verify Orchestrator Agent routing."""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.orchestrator import get_orchestrator_agent

def test_orchestrator():
    """Test orchestrator routing on different medical questions."""
    print("\n" + "="*70)
    print("ORCHESTRATOR AGENT TEST")
    print("="*70 + "\n")

    orchestrator = get_orchestrator_agent()

    # Test cases with different intents
    test_cases = [
        {
            "message": "I have a severe chest pain and difficulty breathing",
            "expected_intent": "triage",
            "description": "Critical symptom - should detect urgency"
        },
        {
            "message": "Can I take ibuprofen with my blood pressure medication?",
            "expected_intent": "medication",
            "description": "Drug interaction question"
        },
        {
            "message": "I have a headache and fever for 3 days",
            "expected_intent": "clinical",
            "description": "Symptom analysis - clinical knowledge"
        },
        {
            "message": "Tell me about treatment guidelines for type 2 diabetes",
            "expected_intent": "rag",
            "description": "Document/literature retrieval"
        },
        {
            "message": "My heart rate has been 110 bpm for the past hour, is that dangerous?",
            "expected_intent": "monitoring",
            "description": "Vital sign analysis"
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*70}")
        print(f"Test {i}: {test['description']}")
        print(f"{'─'*70}")
        print(f"Message: \"{test['message'][:80]}...\"" if len(test['message']) > 80 else f"Message: \"{test['message']}\"")

        # Check for critical symptoms first
        is_critical = orchestrator.should_escalate_to_triage(test['message'])
        if is_critical:
            print(f"✅ CRITICAL: Escalated to triage")
            continue

        # Get routing
        try:
            routing = orchestrator.route_message(test['message'])

            agent = routing.get('agent_to_call', 'unknown').replace('_agent', '')
            confidence = routing.get('confidence', 0.0)
            reason = routing.get('reason', 'Unknown')

            print(f"Agent: {agent.upper()}")
            print(f"Confidence: {confidence:.0%}")
            print(f"Reason: {reason}")

            # Check if routing matches expectation
            if agent == test['expected_intent'].replace('_', ''):
                print(f"✅ CORRECT: Matched expected intent '{test['expected_intent']}'")
            else:
                print(f"⚠️  Routed to '{agent}', expected '{test['expected_intent']}'")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print(f"\n{'─'*70}")
    print("TEST COMPLETE")
    print(f"{'─'*70}\n")

if __name__ == "__main__":
    test_orchestrator()
