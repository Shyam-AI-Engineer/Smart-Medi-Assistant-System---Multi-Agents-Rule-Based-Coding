"""Tests for access control / IDOR protection (critical path: data isolation).

These tests verify:
- Patients can only read their own data (not another patient's).
- Doctors can only access patients they are explicitly assigned to.
- Admins bypass the assignment check and can access any patient.
- Unauthenticated requests are rejected before any data access.
"""
import pytest

from app.models import Patient
from tests.conftest import make_user, auth_header


# ---------------------------------------------------------------------------
# Unauthenticated access
# ---------------------------------------------------------------------------

class TestUnauthenticatedRejection:
    def test_vitals_endpoint_requires_token(self, client, patient_record):
        resp = client.get(f"/api/v1/vitals/{patient_record.id}")
        assert resp.status_code == 401

    def test_doctor_endpoint_requires_token(self, client, patient_record):
        resp = client.get(f"/api/v1/doctor/patients/{patient_record.id}")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Patient data ownership
# ---------------------------------------------------------------------------

class TestPatientDataOwnership:
    """A patient may only access their own records."""

    def test_patient_can_read_own_vitals(self, client, patient_record, patient_headers):
        resp = client.get(f"/api/v1/vitals/{patient_record.id}", headers=patient_headers)
        # 200 with empty list — no vitals yet
        assert resp.status_code == 200

    def test_patient_cannot_read_another_patients_vitals(
        self, client, db, patient_headers, second_patient_record
    ):
        # Patient A tries to fetch Patient B's vitals
        resp = client.get(
            f"/api/v1/vitals/{second_patient_record.id}",
            headers=patient_headers,
        )
        assert resp.status_code == 403

    def test_second_patient_cannot_read_first_patients_vitals(
        self, client, db, second_patient_headers, patient_record
    ):
        resp = client.get(
            f"/api/v1/vitals/{patient_record.id}",
            headers=second_patient_headers,
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Doctor–patient assignment (IDOR fix)
# ---------------------------------------------------------------------------

class TestDoctorPatientIDOR:
    """Doctors can only access patients they are assigned to."""

    def test_doctor_cannot_access_unassigned_patient(
        self, client, doctor_headers, patient_record
    ):
        resp = client.get(
            f"/api/v1/doctor/patients/{patient_record.id}",
            headers=doctor_headers,
        )
        assert resp.status_code == 403

    def test_doctor_can_access_patient_after_assignment(
        self,
        client,
        doctor_user,
        doctor_headers,
        patient_record,
        admin_headers,
    ):
        # Admin creates the assignment
        assign_resp = client.post(
            "/api/v1/admin/assignments",
            json={"doctor_user_id": doctor_user.id, "patient_id": patient_record.id},
            headers=admin_headers,
        )
        assert assign_resp.status_code == 201

        # Doctor can now access that patient
        resp = client.get(
            f"/api/v1/doctor/patients/{patient_record.id}",
            headers=doctor_headers,
        )
        assert resp.status_code == 200

    def test_assignment_is_specific_to_doctor(
        self,
        client,
        db,
        patient_record,
        admin_headers,
    ):
        # Create two doctors; assign only doctor_1 to the patient
        doctor_1 = make_user(db, "doctor1@test.com", "doctor", "Dr. One")
        doctor_2 = make_user(db, "doctor2@test.com", "doctor", "Dr. Two")

        client.post(
            "/api/v1/admin/assignments",
            json={"doctor_user_id": doctor_1.id, "patient_id": patient_record.id},
            headers=admin_headers,
        )

        # Doctor 2 (not assigned) is still blocked
        resp = client.get(
            f"/api/v1/doctor/patients/{patient_record.id}",
            headers=auth_header(doctor_2),
        )
        assert resp.status_code == 403

        # Doctor 1 (assigned) is allowed
        resp = client.get(
            f"/api/v1/doctor/patients/{patient_record.id}",
            headers=auth_header(doctor_1),
        )
        assert resp.status_code == 200

    def test_duplicate_assignment_returns_409(
        self, client, doctor_user, patient_record, admin_headers
    ):
        payload = {"doctor_user_id": doctor_user.id, "patient_id": patient_record.id}
        client.post("/api/v1/admin/assignments", json=payload, headers=admin_headers)
        resp = client.post("/api/v1/admin/assignments", json=payload, headers=admin_headers)
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# Admin access
# ---------------------------------------------------------------------------

class TestAdminAccess:
    def test_admin_bypasses_assignment_check(
        self, client, admin_headers, patient_record
    ):
        # Admin has no assignment row but should still get 200
        resp = client.get(
            f"/api/v1/doctor/patients/{patient_record.id}",
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_admin_can_list_assignments(self, client, admin_headers):
        resp = client.get("/api/v1/admin/assignments", headers=admin_headers)
        assert resp.status_code == 200

    def test_non_admin_cannot_create_assignment(
        self, client, doctor_user, patient_record, doctor_headers
    ):
        resp = client.post(
            "/api/v1/admin/assignments",
            json={"doctor_user_id": doctor_user.id, "patient_id": patient_record.id},
            headers=doctor_headers,
        )
        assert resp.status_code == 403

    def test_patient_cannot_access_doctor_route(
        self, client, patient_headers, patient_record
    ):
        resp = client.get(
            f"/api/v1/doctor/patients/{patient_record.id}",
            headers=patient_headers,
        )
        assert resp.status_code == 403
