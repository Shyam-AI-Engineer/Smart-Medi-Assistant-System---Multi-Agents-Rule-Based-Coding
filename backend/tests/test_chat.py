"""Tests for /api/v1/chat endpoints (send message, history, access control)."""
import pytest
from unittest.mock import patch

from tests.conftest import make_user, auth_header

CHAT_SEND = "/api/v1/chat"
CHAT_HISTORY = "/api/v1/chat/history"

MOCK_AGENT_RESPONSE = {
    "response": "Your symptoms may indicate a common cold. Please rest and stay hydrated.",
    "sources": [],
    "agent_used": "clinical",
    "confidence_score": 0.85,
    "tokens_used": 150,
    "context_documents_used": 2,
    "error": False,
}

MOCK_HISTORY_RESULT = {
    "items": [
        {
            "id": "chat-id-1",
            "user_message": "I have a headache",
            "ai_response": "This may be due to dehydration.",
            "agent_used": "clinical",
            "confidence_score": 0.85,
            "created_at": "2026-05-06T10:00:00",
        }
    ],
    "total": 1,
    "has_next": False,
}


# ---------------------------------------------------------------------------
# POST /api/v1/chat  — send message
# ---------------------------------------------------------------------------

class TestSendMessage:
    def test_authenticated_patient_gets_ai_response(self, client, patient_headers):
        with patch("app.api.v1.chat.ChatService") as MockSvc:
            MockSvc.return_value.handle_message.return_value = MOCK_AGENT_RESPONSE
            resp = client.post(
                CHAT_SEND,
                json={"message": "I have a headache and mild fever."},
                headers=patient_headers,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "response" in body
        assert body["agent_used"] == "clinical"
        assert body["confidence_score"] == 0.85
        assert body["error"] is False

    def test_unauthenticated_request_rejected(self, client):
        resp = client.post(CHAT_SEND, json={"message": "I have a headache"})
        assert resp.status_code == 401

    def test_whitespace_only_message_returns_400(self, client, patient_headers):
        with patch("app.api.v1.chat.ChatService"):
            resp = client.post(
                CHAT_SEND,
                json={"message": "   "},
                headers=patient_headers,
            )
        assert resp.status_code == 400

    def test_message_exceeding_max_length_returns_422(self, client, patient_headers):
        resp = client.post(
            CHAT_SEND,
            json={"message": "x" * 5001},
            headers=patient_headers,
        )
        assert resp.status_code == 422

    def test_missing_message_field_returns_422(self, client, patient_headers):
        resp = client.post(CHAT_SEND, json={}, headers=patient_headers)
        assert resp.status_code == 422

    def test_response_contains_required_fields(self, client, patient_headers):
        with patch("app.api.v1.chat.ChatService") as MockSvc:
            MockSvc.return_value.handle_message.return_value = MOCK_AGENT_RESPONSE
            resp = client.post(
                CHAT_SEND,
                json={"message": "What causes high blood pressure?"},
                headers=patient_headers,
            )
        assert resp.status_code == 200
        body = resp.json()
        for field in ("response", "agent_used", "confidence_score", "sources", "error"):
            assert field in body, f"Missing field: {field}"

    def test_doctor_can_also_send_message(self, client, doctor_headers):
        with patch("app.api.v1.chat.ChatService") as MockSvc:
            MockSvc.return_value.handle_message.return_value = MOCK_AGENT_RESPONSE
            resp = client.post(
                CHAT_SEND,
                json={"message": "What are the symptoms of diabetes?"},
                headers=doctor_headers,
            )
        # Doctors also have patient profiles (created in make_user), so this works
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/chat/history  — chat history
# ---------------------------------------------------------------------------

class TestChatHistory:
    def test_patient_can_retrieve_own_history(self, client, patient_headers):
        with patch("app.api.v1.chat.ChatService") as MockSvc:
            MockSvc.return_value.get_chat_history.return_value = MOCK_HISTORY_RESULT
            resp = client.get(CHAT_HISTORY, headers=patient_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total"] == 1
        assert body["has_next"] is False

    def test_unauthenticated_history_rejected(self, client):
        resp = client.get(CHAT_HISTORY)
        assert resp.status_code == 401

    def test_user_without_patient_profile_gets_404(self, client, db):
        # Admin users have no patient profile
        admin = make_user(db, "admin_chat_test@test.com", "admin")
        resp = client.get(CHAT_HISTORY, headers=auth_header(admin))
        assert resp.status_code == 404

    def test_empty_history_returns_empty_list(self, client, patient_headers):
        empty_result = {"items": [], "total": 0, "has_next": False}
        with patch("app.api.v1.chat.ChatService") as MockSvc:
            MockSvc.return_value.get_chat_history.return_value = empty_result
            resp = client.get(CHAT_HISTORY, headers=patient_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    def test_pagination_params_forwarded_to_service(self, client, patient_headers):
        with patch("app.api.v1.chat.ChatService") as MockSvc:
            MockSvc.return_value.get_chat_history.return_value = {
                "items": [],
                "total": 0,
                "has_next": False,
            }
            resp = client.get(
                f"{CHAT_HISTORY}?limit=5&offset=10",
                headers=patient_headers,
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["limit"] == 5
        assert body["offset"] == 10

    def test_invalid_token_rejected(self, client):
        resp = client.get(
            CHAT_HISTORY,
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401
