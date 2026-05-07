"""Tests for /api/v1/auth/* endpoints (critical path: authentication)."""
import pytest

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"

VALID_USER = {
    "email": "alice@example.com",
    "password": "Password1!",
    "full_name": "Alice Smith",
    "role": "patient",
}


# ---------------------------------------------------------------------------
# Health / root
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegister:
    def test_success_returns_201_with_tokens(self, client):
        resp = client.post(REGISTER, json=VALID_USER)
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["role"] == "patient"
        assert body["email"] == VALID_USER["email"]

    def test_duplicate_email_returns_409(self, client):
        client.post(REGISTER, json=VALID_USER)
        resp = client.post(REGISTER, json=VALID_USER)
        assert resp.status_code == 409

    def test_password_too_short_returns_422(self, client):
        resp = client.post(REGISTER, json={**VALID_USER, "password": "short"})
        assert resp.status_code == 422

    def test_missing_email_returns_422(self, client):
        payload = {k: v for k, v in VALID_USER.items() if k != "email"}
        resp = client.post(REGISTER, json=payload)
        assert resp.status_code == 422

    def test_invalid_email_format_returns_422(self, client):
        resp = client.post(REGISTER, json={**VALID_USER, "email": "not-an-email"})
        assert resp.status_code == 422

    def test_register_as_doctor_role(self, client):
        payload = {**VALID_USER, "email": "doctor@example.com", "role": "doctor"}
        resp = client.post(REGISTER, json=payload)
        assert resp.status_code == 201
        assert resp.json()["role"] == "doctor"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_success_returns_200_with_tokens(self, client):
        client.post(REGISTER, json=VALID_USER)
        resp = client.post(
            LOGIN,
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["role"] == "patient"

    def test_wrong_password_returns_401(self, client):
        client.post(REGISTER, json=VALID_USER)
        resp = client.post(
            LOGIN,
            json={"email": VALID_USER["email"], "password": "WrongPass!"},
        )
        assert resp.status_code == 401

    def test_unknown_email_returns_401(self, client):
        resp = client.post(
            LOGIN,
            json={"email": "nobody@example.com", "password": "Password1!"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me (token introspection)
# ---------------------------------------------------------------------------

class TestMe:
    def test_authenticated_user_gets_own_profile(self, client, patient_user, patient_headers):
        resp = client.get(ME, headers=patient_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == patient_user.email
        assert body["role"] == "patient"
        assert body["is_active"] is True

    def test_no_token_returns_401(self, client):
        resp = client.get(ME)
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        resp = client.get(ME, headers={"Authorization": "Bearer this.is.garbage"})
        assert resp.status_code == 401

    def test_doctor_me_shows_doctor_role(self, client, doctor_user, doctor_headers):
        resp = client.get(ME, headers=doctor_headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "doctor"

    def test_admin_me_shows_admin_role(self, client, admin_user, admin_headers):
        resp = client.get(ME, headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------

class TestRefreshToken:
    def test_valid_refresh_token_issues_new_access_token(self, client):
        register_resp = client.post(REGISTER, json=VALID_USER)
        refresh_tok = register_resp.json()["refresh_token"]

        resp = client.post(REFRESH, headers={"Authorization": f"Bearer {refresh_tok}"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_access_token_cannot_be_used_as_refresh(self, client):
        register_resp = client.post(REGISTER, json=VALID_USER)
        access_tok = register_resp.json()["access_token"]

        resp = client.post(REFRESH, headers={"Authorization": f"Bearer {access_tok}"})
        assert resp.status_code == 401

    def test_garbage_refresh_token_returns_401(self, client):
        resp = client.post(REFRESH, headers={"Authorization": "Bearer garbage.token.here"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout and token revocation
# ---------------------------------------------------------------------------

class TestLogout:
    def test_authenticated_user_can_logout(self, client, patient_headers):
        """Logout succeeds for authenticated user."""
        resp = client.post(LOGOUT, headers=patient_headers)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_logout_without_token_returns_401(self, client):
        """Logout without auth fails."""
        resp = client.post(LOGOUT)
        assert resp.status_code == 401

    def test_revoked_token_rejected_on_next_request(self, client, patient_headers, patient_user):
        """After logout, token is rejected."""
        # First: logout
        logout_resp = client.post(LOGOUT, headers=patient_headers)
        assert logout_resp.status_code == 200

        # Second: try to use same token on /me endpoint
        me_resp = client.get(ME, headers=patient_headers)
        assert me_resp.status_code == 401
        assert "revoked" in me_resp.json()["detail"].lower()

    def test_new_token_after_logout_works(self, client):
        """User can login again after logout and get new token."""
        # Register user
        register_resp = client.post(REGISTER, json=VALID_USER)
        old_token = register_resp.json()["access_token"]
        old_headers = {"Authorization": f"Bearer {old_token}"}

        # Verify token works
        me_resp = client.get(ME, headers=old_headers)
        assert me_resp.status_code == 200

        # Logout
        logout_resp = client.post(LOGOUT, headers=old_headers)
        assert logout_resp.status_code == 200

        # Old token is revoked
        me_resp = client.get(ME, headers=old_headers)
        assert me_resp.status_code == 401

        # Login again
        login_resp = client.post(
            LOGIN,
            json={"email": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        assert login_resp.status_code == 200
        new_token = login_resp.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}

        # New token works
        me_resp = client.get(ME, headers=new_headers)
        assert me_resp.status_code == 200

    def test_logout_logs_audit_trail(self, client, db, patient_headers, patient_user):
        """Logout action is logged to audit_logs."""
        from app.models import AuditLog

        resp = client.post(LOGOUT, headers=patient_headers)
        assert resp.status_code == 200

        # Verify audit log
        audit_logs = db.query(AuditLog).filter_by(
            user_id=patient_user.id,
            action="logout",
            resource_type="auth",
        ).all()

        assert len(audit_logs) == 1
        log = audit_logs[0]
        assert log.user_email == patient_user.email
        assert log.user_role == "patient"
        assert log.outcome == "success"
