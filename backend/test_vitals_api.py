"""Integration tests for POST /api/v1/vitals/analyze endpoint."""
import pytest
from fastapi.testclient import TestClient
from app import app
from app.middleware.auth_middleware import create_access_token

client = TestClient(app)

# Test JWT token for authenticated requests
TEST_USER_ID = "test-user-123"
TEST_EMAIL = "test@example.com"
TEST_ROLE = "patient"
TEST_TOKEN = create_access_token(TEST_USER_ID, TEST_EMAIL, TEST_ROLE)
AUTH_HEADERS = {"Authorization": f"Bearer {TEST_TOKEN}"}


class TestVitalsAnalyzeEndpoint:
    """Tests for POST /api/v1/vitals/analyze"""

    def test_analyze_normal_vitals(self):
        """Test analysis of normal vital signs."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 75,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "oxygen_saturation": 98,
                "temperature": 37.0,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "NORMAL"
        assert data["severity_level"] == 1
        assert data["should_escalate_to_triage"] is False
        assert data["agent_used"] == "monitoring"
        assert len(data["vital_analyses"]) > 0
        assert data["error"] is False

    def test_analyze_moderate_vitals(self):
        """Test analysis of moderately elevated vitals."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 110,  # Elevated but not HIGH
                "blood_pressure_systolic": 130,  # Elevated
                "oxygen_saturation": 96,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] in ["MODERATE", "HIGH"]  # Agent may classify as either
        assert data["severity_level"] >= 2
        assert data["error"] is False

    def test_analyze_high_vitals(self):
        """Test analysis of high-risk vitals with escalation."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 145,
                "blood_pressure_systolic": 155,
                "blood_pressure_diastolic": 98,
                "oxygen_saturation": 96,
                "temperature": 38.5,
                "respiratory_rate": 22,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        # Multiple HIGH vitals could be classified as HIGH or CRITICAL
        assert data["overall_status"] in ["HIGH", "CRITICAL"]
        assert data["severity_level"] >= 3
        assert data["should_escalate_to_triage"] is True  # HIGH/CRITICAL severity escalates
        assert data["error"] is False
        assert len(data["recommendations"]) > 0

    def test_analyze_critical_vitals(self):
        """Test analysis of critical vitals with emergency escalation."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 35,  # Critically low
                "oxygen_saturation": 82,  # Critically low
                "temperature": 34.0,  # Critically low
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] == "CRITICAL"
        assert data["severity_level"] == 4
        assert data["should_escalate_to_triage"] is True  # CRITICAL severity escalates
        assert data["error"] is False
        assert len(data["critical_findings"]) > 0

    def test_analyze_with_patient_info(self):
        """Test analysis with patient context information."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 90,
                "blood_pressure_systolic": 125,
                "patient_info": {
                    "age": 75,
                    "medical_history": "Hypertension, Type 2 Diabetes",
                    "current_medications": "Metformin, Lisinopril",
                },
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] in ["NORMAL", "MODERATE", "HIGH", "CRITICAL"]
        assert data["error"] is False

    def test_analyze_no_vitals_provided(self):
        """Test error handling when no vitals are provided."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={},
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 400
        data = response.json()
        assert "vital" in data["detail"].lower()

    def test_analyze_all_vitals_none(self):
        """Test error handling when all vitals are None."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": None,
                "blood_pressure_systolic": None,
                "blood_pressure_diastolic": None,
                "oxygen_saturation": None,
                "temperature": None,
                "respiratory_rate": None,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 400
        data = response.json()
        assert "vital" in data["detail"].lower()

    def test_analyze_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 100,
                "blood_pressure_systolic": 120,
            },
        )

        # HTTPBearer returns 403 for missing credentials, 401 for invalid
        assert response.status_code in [401, 403]

    def test_analyze_invalid_jwt(self):
        """Test that invalid JWT tokens are rejected."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 100,
                "blood_pressure_systolic": 120,
            },
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        # HTTPBearer returns 401 for invalid token format/content
        assert response.status_code == 401

    def test_analyze_invalid_heart_rate_too_high(self):
        """Test validation of heart rate upper bound."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 500,  # Invalid: > 300
                "blood_pressure_systolic": 120,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_analyze_invalid_temperature_too_low(self):
        """Test validation of temperature lower bound."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "temperature": 25.0,  # Invalid: < 30.0
                "heart_rate": 80,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_analyze_single_vital(self):
        """Test analysis with just one vital sign."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 160,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] in ["NORMAL", "MODERATE", "HIGH", "CRITICAL"]
        assert len(data["vital_analyses"]) == 1
        assert data["vital_analyses"][0]["vital_type"] == "heart_rate"

    def test_analyze_response_format(self):
        """Test that response includes all required fields."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 100,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "oxygen_saturation": 95,
                "temperature": 37.0,
                "respiratory_rate": 16,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required response fields
        required_fields = [
            "overall_status",
            "severity_level",
            "vital_analyses",
            "critical_findings",
            "overall_assessment",
            "recommendations",
            "should_escalate_to_triage",
            "confidence_score",
            "agent_used",
            "tokens_used",
            "timestamp",
            "disclaimer",
            "response",
            "error",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify response structure
        assert isinstance(data["overall_status"], str)
        assert isinstance(data["severity_level"], int)
        assert 1 <= data["severity_level"] <= 4
        assert isinstance(data["vital_analyses"], list)
        assert isinstance(data["critical_findings"], list)
        assert isinstance(data["recommendations"], list)
        assert isinstance(data["should_escalate_to_triage"], bool)
        assert 0 <= data["confidence_score"] <= 1

        # Verify vital analysis structure
        for vital in data["vital_analyses"]:
            assert "vital_type" in vital
            assert "value" in vital
            assert "unit" in vital
            assert "status" in vital
            assert "severity" in vital
            assert "normal_range" in vital
            assert "explanation" in vital
            assert "recommendation" in vital
            assert "confidence" in vital

    def test_analyze_hypoxia_scenario(self):
        """Test critical hypoxia scenario."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 120,
                "oxygen_saturation": 82,  # Critical hypoxia
                "blood_pressure_systolic": 95,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        # Low O2 + elevated HR + low BP = CRITICAL
        assert data["overall_status"] in ["HIGH", "CRITICAL"]  # At least HIGH due to low O2
        assert data["should_escalate_to_triage"] is True

    def test_analyze_high_fever_scenario(self):
        """Test high fever scenario."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "temperature": 39.5,  # High fever
                "heart_rate": 95,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_status"] in ["MODERATE", "HIGH"]
        # Fever alone doesn't always escalate, depends on other factors

    def test_analyze_floating_point_values(self):
        """Test handling of floating point vital values."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 72.5,
                "temperature": 36.7,
                "oxygen_saturation": 97.5,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["error"] is False


class TestVitalsEndpointIntegration:
    """Integration tests for vitals endpoint with other components."""

    def test_multiple_sequential_analyses(self):
        """Test multiple analyses in sequence."""
        # First analysis
        response1 = client.post(
            "/api/v1/vitals/analyze",
            json={"heart_rate": 80},
            headers=AUTH_HEADERS,
        )
        assert response1.status_code == 200

        # Second analysis
        response2 = client.post(
            "/api/v1/vitals/analyze",
            json={"heart_rate": 140},
            headers=AUTH_HEADERS,
        )
        assert response2.status_code == 200

        # Verify different results
        data1 = response1.json()
        data2 = response2.json()
        assert data1["overall_status"] != data2["overall_status"]

    def test_response_includes_medical_explanation(self):
        """Test that response includes patient-friendly medical explanation."""
        response = client.post(
            "/api/v1/vitals/analyze",
            json={
                "heart_rate": 140,
                "temperature": 38.5,
            },
            headers=AUTH_HEADERS,
        )

        assert response.status_code == 200
        data = response.json()

        # Check for medical explanations
        assert len(data["overall_assessment"]) > 0
        assert len(data["response"]) > 0
        assert "VITAL SIGNS ANALYSIS" in data["response"]
        assert len(data["disclaimer"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
