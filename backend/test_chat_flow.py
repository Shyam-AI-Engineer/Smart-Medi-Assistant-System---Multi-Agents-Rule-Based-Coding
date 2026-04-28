#!/usr/bin/env python3
"""Diagnostic script - test full chat flow and show actual responses."""
import sys
import json
from app.extensions import SessionLocal
from app.models import User, Patient
from app.services.chat_service import ChatService

def test_chat():
    """Test chat endpoint directly."""
    db = SessionLocal()

    try:
        # Get first patient
        patient = db.query(Patient).first()
        if not patient:
            print("❌ No patient found in database")
            return

        print(f"✓ Found patient: {patient.id}")
        print(f"✓ User ID: {patient.user_id}")

        # Create ChatService
        service = ChatService(db)
        print("✓ ChatService initialized")

        # Test message
        test_message = "What should I do if I have a high blood pressure?"
        print(f"\n📤 Sending test message: {test_message}\n")

        # Call handle_message directly
        response = service.handle_message(
            message=test_message,
            user_id=patient.user_id,
            patient_id=patient.id,
        )

        # Pretty print response
        print("=" * 80)
        print("RESPONSE STRUCTURE:")
        print("=" * 80)
        for key, value in response.items():
            if key == "response":
                print(f"  {key}: {str(value)[:200]}...")
            else:
                print(f"  {key}: {value}")

        # Check for error
        if response.get("error"):
            print("\n⚠️ AGENT RETURNED ERROR")
            print(f"Message: {response.get('response')}")
        else:
            print("\n✓ Agent returned success")

        # Check if message was saved
        from app.models import ChatHistory
        saved = db.query(ChatHistory).filter_by(patient_id=patient.id).order_by(ChatHistory.created_at.desc()).first()

        if saved and test_message in saved.user_message:
            print(f"\n✓ Message SAVED to database")
            print(f"  Saved message: {saved.user_message[:100]}")
            print(f"  Saved response: {saved.ai_response[:100]}")
        else:
            print(f"\n❌ Message NOT SAVED to database")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_chat()
