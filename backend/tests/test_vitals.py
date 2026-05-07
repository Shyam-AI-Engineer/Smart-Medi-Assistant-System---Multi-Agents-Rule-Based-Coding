"""Tests for /api/v1/vitals/* endpoints (store, history, access control)."""
import uuid
from unittest.mock import patch

from app.models.vitals import Vitals

VITALS_STORE = "/api/v1/vitals/"

VALID_PAYLOAD = {
    "heart_rate": 72.0,
    "blood_pressure_systolic": 120.0,
    "blood_pressure_diastolic": 80.0,
    "oxygen_saturation": 98.0,
    "temperature": 36.6,
}

MOCK_ANALYSIS = {
    "overall_status": "NORMAL",
    "severity_level": 1,
    "should_escalate_to_triage": False,
    "vital_analyses": [],
    "overall_assessment": "Vitals are within normal range.",
    "recommendations": [],
    "critical_findings": [],
    "confidence_score": 0.95,
    "agent_used": "monitoring",
    "tokens_used": 0,
    "timestamp": "2026-05-06T10:00:00",
    "disclaimer": "For informational purposes only.",
    "response": "Your vitals are normal.",
}


def _insert_vitals(db, patient_id: str, **overrides) -> Vitals:
    """Insert a Vitals row directly into the test DB."""
    v = Vitals(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        heart_rate=overrides.get("heart_rate", 72),
        blood_pressure_systolic=overrides.get("blood_pressure_systolic", 120),
        blood_pressure_diastolic=overrides.get("blood_pressure_diastolic", 80),
        oxygen_saturation=overrides.get("oxygen_saturation", 98.0),
        temperature=overrides.get("temperature", 36.6),
        anomaly_detected=overrides.get("anomaly_detected", False),
        anomaly_score=overrides.get("anomaly_score", None),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def _mock_store_result(vitals_record: Vitals) -> dict:
    return {"record": vitals_record, "analysis": MOCK_ANALYSIS, "trend": "STABLE"}


# ---------------------------------------------------------------------------
# POST /api/v1/vitals/  — store vitals
# ---------------------------------------------------------------------------

class TestStoreVitals:
    def test_patient_can_store_vitals(self, client, db, patient_record, patient_headers):
        record = _insert_vitals(db, patient_record.id)
        with patch("app.api.v1.vitals.VitalsService") as MockSvc:
            MockSvc.return_value.store_and_analyze.return_value = _mock_store_result(record)
            resp = client.post(VITALS_STORE, json=VALID_PAYLOAD, headers=patient_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert "record" in body
        assert "analysis" in body
        assert body["trend"] == "STABLE"

    def test_store_requires_authentication(self, client):
        resp = client.post(VITALS_STORE, json=VALID_PAYLOAD)
        assert resp.status_code == 401

    def test_no_patient_profile_returns_404(self, client, admin_headers):
        # Admin accounts have no patient profile → 404
        resp = client.post(VITALS_STORE, json=VALID_PAYLOAD, headers=admin_headers)
        assert resp.status_code == 404

    def test_out_of_range_heart_rate_returns_422(self, client, patient_headers):
        resp = client.post(
            VITALS_STORE,
            json={**VALID_PAYLOAD, "heart_rate": 999.0},
            headers=patient_headers,
        )
        assert resp.status_code == 422

    def test_out_of_range_oxygen_saturation_returns_422(self, client, patient_headers):
        resp = client.post(
            VITALS_STORE,
            json={**VALID_PAYLOAD, "oxygen_saturation": 101.0},
            headers=patient_headers,
        )
        assert resp.status_code == 422

    def test_analysis_in_response_includes_overall_status(
        self, client, db, patient_record, patient_headers
    ):
        record = _insert_vitals(db, patient_record.id)
        with patch("app.api.v1.vitals.VitalsService") as MockSvc:
            MockSvc.return_value.store_and_analyze.return_value = _mock_store_result(record)
            resp = client.post(VITALS_STORE, json=VALID_PAYLOAD, headers=patient_headers)
        assert resp.json()["analysis"]["overall_status"] == "NORMAL"


# ---------------------------------------------------------------------------
# GET /api/v1/vitals/{patient_id}  — history
# ---------------------------------------------------------------------------

class TestGetVitalsHistory:
    def test_patient_can_read_own_vitals(self, client, patient_record, patient_headers):
        resp = client.get(f"/api/v1/vitals/{patient_record.id}", headers=patient_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["patient_id"] == patient_record.id
        assert isinstance(body["items"], list)

    def test_empty_history_returns_empty_list(self, client, patient_record, patient_headers):
        resp = client.get(f"/api/v1/vitals/{patient_record.id}", headers=patient_headers)
        assert resp.status_code == 200
        assert resp.json()["items"] == []
        assert resp.json()["total"] == 0

    def test_stored_vitals_appear_in_history(
        self, client, db, patient_record, patient_headers
    ):
        _insert_vitals(db, patient_record.id)
        _insert_vitals(db, patient_record.id)
        resp = client.get(f"/api/v1/vitals/{patient_record.id}", headers=patient_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    def test_pagination_limit_respected(self, client, db, patient_record, patient_headers):
        for _ in range(5):
            _insert_vitals(db, patient_record.id)
        resp = client.get(
            f"/api/v1/vitals/{patient_record.id}?limit=2&offset=0",
            headers=patient_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) == 2
        assert body["has_next"] is True

    def test_pagination_offset_skips_records(self, client, db, patient_record, patient_headers):
        for _ in range(3):
            _insert_vitals(db, patient_record.id)
        resp = client.get(
            f"/api/v1/vitals/{patient_record.id}?limit=10&offset=2",
            headers=patient_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

    def test_patient_cannot_read_another_patients_vitals(
        self, client, second_patient_record, patient_headers
    ):
        resp = client.get(
            f"/api/v1/vitals/{second_patient_record.id}",
            headers=patient_headers,
        )
        assert resp.status_code == 403

    def test_unauthenticated_request_rejected(self, client, patient_record):
        resp = client.get(f"/api/v1/vitals/{patient_record.id}")
        assert resp.status_code == 401

    def test_doctor_can_read_any_patient_vitals(
        self, client, doctor_headers, patient_record
    ):
        resp = client.get(f"/api/v1/vitals/{patient_record.id}", headers=doctor_headers)
        assert resp.status_code == 200

    def test_admin_can_read_any_patient_vitals(
        self, client, admin_headers, patient_record
    ):
        resp = client.get(f"/api/v1/vitals/{patient_record.id}", headers=admin_headers)
        assert resp.status_code == 200

    def test_nonexistent_patient_returns_404(self, client, patient_headers):
        resp = client.get(
            f"/api/v1/vitals/{uuid.uuid4()}",
            headers=patient_headers,
        )
        assert resp.status_code in (403, 404)
