"""Tests for AI agents (critical path: medication, triage, extractors).

Pure-logic tests require no mocking.  LLM-calling tests mock EuriService
so the suite runs without a real EURI_API_KEY.
"""
import os
os.environ.setdefault("JWT_SECRET_KEY", "ci-test-secret-32-chars-minimum!!")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# ChatExtractors — pure functions, no mocking needed
# ---------------------------------------------------------------------------

class TestExtractMedications:
    """extract_medications() finds known drug names in free text."""

    def _run(self, message: str):
        from app.utils.chat_extractors import extract_medications
        return extract_medications(message)

    def test_single_medication_found(self):
        result = self._run("I have been taking ibuprofen for 3 days")
        assert "ibuprofen" in result

    def test_multiple_medications_found(self):
        result = self._run("I take aspirin and warfarin daily")
        assert "aspirin" in result
        assert "warfarin" in result

    def test_case_insensitive(self):
        result = self._run("I take METFORMIN every morning")
        assert "metformin" in result

    def test_no_medications_returns_empty(self):
        result = self._run("I have a headache and runny nose")
        assert result == []

    def test_partial_word_match_included(self):
        # "ibuprofen" appears as substring in message
        result = self._run("My doctor prescribed ibuprofen200mg")
        assert "ibuprofen" in result


class TestExtractVitalsFromMessage:
    """extract_vitals_from_message() parses structured vital numbers."""

    def _run(self, message: str):
        from app.utils.chat_extractors import extract_vitals_from_message
        return extract_vitals_from_message(message)

    def test_heart_rate_extracted(self):
        vitals = self._run("My heart rate: 88 bpm today")
        assert vitals.get("heart_rate") == 88.0

    def test_pulse_keyword_extracted(self):
        vitals = self._run("pulse: 72")
        assert vitals.get("heart_rate") == 72.0

    def test_blood_pressure_extracted(self):
        vitals = self._run("blood pressure: 130/85")
        assert vitals.get("blood_pressure_systolic") == 130.0
        assert vitals.get("blood_pressure_diastolic") == 85.0

    def test_bp_shorthand_extracted(self):
        vitals = self._run("bp: 118/76")
        assert vitals.get("blood_pressure_systolic") == 118.0

    def test_temperature_extracted(self):
        vitals = self._run("temperature: 38.2 degrees")
        assert vitals.get("temperature") == 38.2

    def test_oxygen_saturation_extracted(self):
        vitals = self._run("oxygen: 96 percent")
        assert vitals.get("oxygen_saturation") == 96.0

    def test_spo2_shorthand(self):
        vitals = self._run("spo2: 98")
        assert vitals.get("oxygen_saturation") == 98.0

    def test_respiratory_rate_extracted(self):
        vitals = self._run("respiratory rate: 16")
        assert vitals.get("respiratory_rate") == 16.0

    def test_no_vitals_returns_empty(self):
        vitals = self._run("I feel a bit tired today")
        assert vitals == {}

    def test_multiple_vitals_extracted(self):
        vitals = self._run("hr: 90, bp: 120/80, temp: 37.0")
        assert vitals.get("heart_rate") == 90.0
        assert vitals.get("blood_pressure_systolic") == 120.0
        assert vitals.get("temperature") == 37.0


# ---------------------------------------------------------------------------
# MedicationAgent — rule-based private methods (no LLM)
# ---------------------------------------------------------------------------

@pytest.fixture()
def med_agent():
    """MedicationAgent with Euri service stubbed out."""
    with patch("app.agents.medication_agent.get_euri_service") as mock_euri:
        mock_euri.return_value = MagicMock()
        from app.agents.medication_agent import MedicationAgent
        agent = MedicationAgent()
        agent.euri.client = MagicMock()
        agent.euri.llm_model = "gpt-4o-mini"
        yield agent


class TestMedicationAgentRuleBasedInteractions:
    """_find_interactions_rule_based() uses the static DRUG_INTERACTIONS dict."""

    def test_high_risk_pair_detected(self, med_agent):
        result = med_agent._find_interactions_rule_based(["ibuprofen", "warfarin"])
        assert len(result) == 1
        assert result[0]["risk"] == "HIGH"

    def test_moderate_risk_pair_detected(self, med_agent):
        result = med_agent._find_interactions_rule_based(["ibuprofen", "amlodipine"])
        assert len(result) == 1
        assert result[0]["risk"] == "MODERATE"

    def test_reverse_direction_lookup(self, med_agent):
        # aspirin → ibuprofen and ibuprofen → aspirin should both work
        result = med_agent._find_interactions_rule_based(["aspirin", "ibuprofen"])
        assert len(result) >= 1

    def test_no_interaction_for_safe_pair(self, med_agent):
        result = med_agent._find_interactions_rule_based(["lisinopril", "metoprolol"])
        assert result == []

    def test_single_drug_has_no_interaction(self, med_agent):
        result = med_agent._find_interactions_rule_based(["metformin"])
        assert result == []

    def test_three_drugs_finds_all_pairs(self, med_agent):
        result = med_agent._find_interactions_rule_based(["aspirin", "ibuprofen", "warfarin"])
        assert len(result) >= 2


class TestMedicationAgentDetermineOverallRisk:
    """_determine_overall_risk() picks worst risk level."""

    def test_no_interactions_returns_none(self, med_agent):
        assert med_agent._determine_overall_risk([], []) == "NONE"

    def test_single_high_interaction_returns_high(self, med_agent):
        interactions = [{"drug1": "a", "drug2": "b", "risk": "HIGH"}]
        assert med_agent._determine_overall_risk(interactions, []) == "HIGH"

    def test_moderate_returns_moderate_when_no_high(self, med_agent):
        interactions = [{"drug1": "a", "drug2": "b", "risk": "MODERATE"}]
        assert med_agent._determine_overall_risk(interactions, []) == "MODERATE"

    def test_high_contraindication_overrides_low_interaction(self, med_agent):
        interactions = [{"drug1": "a", "drug2": "b", "risk": "LOW"}]
        contraindications = [{"risk_level": "HIGH"}]
        assert med_agent._determine_overall_risk(interactions, contraindications) == "HIGH"

    def test_mixed_risks_returns_highest(self, med_agent):
        interactions = [
            {"risk": "LOW"},
            {"risk": "MODERATE"},
            {"risk": "HIGH"},
        ]
        assert med_agent._determine_overall_risk(interactions, []) == "HIGH"


class TestMedicationAgentClassify:
    """_classify_medication() maps drug names to classes."""

    def test_ibuprofen_is_nsaid(self, med_agent):
        assert med_agent._classify_medication("ibuprofen") == "nsaid"

    def test_naproxen_is_nsaid(self, med_agent):
        assert med_agent._classify_medication("Naproxen") == "nsaid"

    def test_metformin_classified_correctly(self, med_agent):
        assert med_agent._classify_medication("metformin") == "metformin"

    def test_warfarin_classified_correctly(self, med_agent):
        assert med_agent._classify_medication("warfarin") == "warfarin"

    def test_unknown_drug_returns_lowercase(self, med_agent):
        assert med_agent._classify_medication("SomeDrug") == "somedrug"


class TestMedicationAgentSingleMedication:
    """check_single_medication() combines side effects + patient alerts."""

    def test_known_drug_returns_side_effects(self, med_agent):
        result = med_agent.check_single_medication("ibuprofen")
        assert "side_effects" in result
        assert len(result["side_effects"]) > 0

    def test_unknown_drug_returns_empty_side_effects(self, med_agent):
        result = med_agent.check_single_medication("unknowndrug123")
        assert result["side_effects"] == []

    def test_elderly_patient_gets_alert(self, med_agent):
        result = med_agent.check_single_medication(
            "metformin", patient_info={"age": 70, "medical_history": ""}
        )
        patient_alerts = result["patient_alerts"]
        assert any("elderly" in alert.lower() or "age" in alert.lower() for alert in patient_alerts)

    def test_kidney_condition_gets_alert(self, med_agent):
        result = med_agent.check_single_medication(
            "metformin", patient_info={"age": 45, "medical_history": "chronic kidney disease"}
        )
        assert any("kidney" in a.lower() for a in result["patient_alerts"])

    def test_agent_used_is_medication(self, med_agent):
        result = med_agent.check_single_medication("aspirin")
        assert result["agent_used"] == "medication"

    def test_response_contains_drug_name(self, med_agent):
        result = med_agent.check_single_medication("warfarin")
        assert "warfarin" in result["response"].lower()


class TestMedicationAgentCheckInteractions:
    """check_medication_interactions() with mocked LLM explanation."""

    def test_high_risk_pair_reflected_in_result(self, med_agent):
        med_agent.euri.client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="These interact due to bleeding risk."))]
        )
        result = med_agent.check_medication_interactions(["ibuprofen", "warfarin"])
        assert result["overall_risk"] == "HIGH"
        assert len(result["interactions"]) >= 1

    def test_safe_combination_returns_none(self, med_agent):
        result = med_agent.check_medication_interactions(["lisinopril", "metoprolol"])
        assert result["overall_risk"] == "NONE"
        assert result["interactions"] == []

    def test_result_contains_required_keys(self, med_agent):
        med_agent.euri.client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Interaction explanation."))]
        )
        result = med_agent.check_medication_interactions(["aspirin", "ibuprofen"])
        for key in ("interaction_risk", "drugs_identified", "interactions", "overall_risk",
                    "agent_used", "response", "disclaimer"):
            assert key in result, f"Missing key: {key}"

    def test_euri_failure_returns_fallback(self, med_agent):
        med_agent._find_interactions_rule_based = MagicMock(side_effect=RuntimeError("DB error"))
        result = med_agent.check_medication_interactions(["ibuprofen", "warfarin"])
        assert result["agent_used"] == "medication"
        assert "error" in result or result["interaction_risk"] == "MODERATE"


# ---------------------------------------------------------------------------
# TriageAgent — pure helpers (no LLM)
# ---------------------------------------------------------------------------

@pytest.fixture()
def triage_agent():
    """TriageAgent with Euri service stubbed out."""
    with patch("app.agents.triage_agent.get_euri_service") as mock_euri:
        mock_euri.return_value = MagicMock()
        from app.agents.triage_agent import TriageAgent
        yield TriageAgent()


class TestTriageAgentIdentifyAbnormalVitals:
    """_identify_abnormal_vitals() flags out-of-range readings."""

    def test_normal_vitals_returns_empty(self, triage_agent):
        vitals = {
            "heart_rate": 72,
            "blood_pressure_systolic": 115,
            "blood_pressure_diastolic": 75,
            "temperature": 37.0,
            "oxygen_saturation": 98,
        }
        assert triage_agent._identify_abnormal_vitals(vitals) == []

    def test_high_heart_rate_flagged(self, triage_agent):
        abnormal = triage_agent._identify_abnormal_vitals({"heart_rate": 110})
        assert any("heart rate" in a.lower() for a in abnormal)

    def test_low_heart_rate_flagged(self, triage_agent):
        abnormal = triage_agent._identify_abnormal_vitals({"heart_rate": 45})
        assert any("heart rate" in a.lower() for a in abnormal)

    def test_high_blood_pressure_flagged(self, triage_agent):
        abnormal = triage_agent._identify_abnormal_vitals({
            "blood_pressure_systolic": 150,
            "blood_pressure_diastolic": 95,
        })
        assert any("blood pressure" in a.lower() for a in abnormal)

    def test_fever_flagged(self, triage_agent):
        abnormal = triage_agent._identify_abnormal_vitals({"temperature": 38.5})
        assert any("temperature" in a.lower() or "fever" in a.lower() for a in abnormal)

    def test_low_oxygen_saturation_flagged(self, triage_agent):
        abnormal = triage_agent._identify_abnormal_vitals({"oxygen_saturation": 92})
        assert any("oxygen" in a.lower() for a in abnormal)

    def test_multiple_abnormal_values(self, triage_agent):
        vitals = {"heart_rate": 130, "temperature": 39.5, "oxygen_saturation": 89}
        abnormal = triage_agent._identify_abnormal_vitals(vitals)
        assert len(abnormal) >= 2


class TestTriageAgentBuildPatientResponse:
    """_build_patient_response() returns level-appropriate text."""

    def test_critical_response_contains_emergency_text(self, triage_agent):
        resp = triage_agent._build_patient_response(
            urgency_level="critical",
            severity_score=9,
            escalation_path="ER",
            immediate_action="Call 108",
            warning_signs=["chest pain"],
        )
        assert "critical" in resp.lower() or "immediate" in resp.lower() or "emergency" in resp.lower()

    def test_urgent_response_contains_urgent_text(self, triage_agent):
        resp = triage_agent._build_patient_response(
            urgency_level="urgent",
            severity_score=7,
            escalation_path="Urgent Care",
            immediate_action="See a doctor",
            warning_signs=["shortness of breath"],
        )
        assert "urgent" in resp.lower()

    def test_self_care_response_does_not_say_critical(self, triage_agent):
        resp = triage_agent._build_patient_response(
            urgency_level="self-care",
            severity_score=2,
            escalation_path="Self-Care",
            immediate_action="Rest and drink fluids",
            warning_signs=[],
        )
        assert "critical" not in resp.lower()
        assert "self" in resp.lower() or "care" in resp.lower()

    def test_moderate_response_mentions_doctor(self, triage_agent):
        resp = triage_agent._build_patient_response(
            urgency_level="moderate",
            severity_score=5,
            escalation_path="Doctor Visit",
            immediate_action="Schedule appointment",
            warning_signs=["persistent headache"],
        )
        assert "doctor" in resp.lower() or "appointment" in resp.lower()


class TestTriageAgentAssessUrgency:
    """assess_urgency() with mocked Euri service."""

    def test_normal_assessment_returns_required_keys(self, triage_agent):
        triage_agent.euri.generate_triage_assessment.return_value = {
            "urgency_level": "moderate",
            "severity_score": 5,
            "escalation_path": "Doctor Visit",
            "warning_signs": ["headache"],
            "immediate_action": "Schedule a visit",
            "reasoning": "Headache may need evaluation",
            "next_steps": ["See doctor"],
            "confidence_score": 0.88,
        }
        result = triage_agent.assess_urgency("I have a bad headache")
        for key in ("urgency_level", "severity_score", "requires_escalation",
                    "escalation_path", "agent_used", "response", "disclaimer"):
            assert key in result

    def test_critical_level_sets_requires_escalation_true(self, triage_agent):
        triage_agent.euri.generate_triage_assessment.return_value = {
            "urgency_level": "critical",
            "severity_score": 9,
            "escalation_path": "ER",
            "warning_signs": ["chest pain"],
            "immediate_action": "Call 108",
            "reasoning": "Cardiac risk",
            "next_steps": [],
            "confidence_score": 0.98,
        }
        result = triage_agent.assess_urgency("Chest pain and can't breathe")
        assert result["requires_escalation"] is True

    def test_self_care_level_sets_requires_escalation_false(self, triage_agent):
        triage_agent.euri.generate_triage_assessment.return_value = {
            "urgency_level": "self-care",
            "severity_score": 2,
            "escalation_path": "Self-Care",
            "warning_signs": [],
            "immediate_action": "Rest",
            "reasoning": "Minor symptoms",
            "next_steps": [],
            "confidence_score": 0.9,
        }
        result = triage_agent.assess_urgency("I have a mild runny nose")
        assert result["requires_escalation"] is False

    def test_euri_failure_returns_fallback_with_escalation(self, triage_agent):
        triage_agent.euri.generate_triage_assessment.side_effect = RuntimeError("API down")
        result = triage_agent.assess_urgency("Some symptom")
        assert result["requires_escalation"] is True
        assert result["agent_used"] == "triage"
        assert "error" in result
