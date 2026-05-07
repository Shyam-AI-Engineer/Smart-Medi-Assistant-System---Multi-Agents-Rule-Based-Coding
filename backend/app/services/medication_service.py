"""Service layer for medication CRUD and interaction checking."""
import logging
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Medication, Patient
from app.agents.medication_agent import get_medication_agent
from app.utils.cache import cache_get, cache_set, cache_delete

logger = logging.getLogger(__name__)

_MED_LIST_TTL = 600       # 10 minutes
_INTERACTION_TTL = 900    # 15 minutes


def _med_list_key(patient_id: str) -> str:
    return f"meds:list:{patient_id}"


def _interaction_key(patient_id: str) -> str:
    return f"meds:interactions:{patient_id}"


class MedicationService:
    def __init__(self, db: Session):
        self.db = db
        self.agent = get_medication_agent()

    def add_medication(self, patient_id: str, data: Dict) -> Medication:
        med = Medication(
            patient_id=patient_id,
            medication_name=data["medication_name"],
            dosage=data["dosage"],
            frequency=data["frequency"],
            start_date=data["start_date"],
            end_date=data.get("end_date"),
            notes=data.get("notes"),
        )
        self.db.add(med)
        self.db.commit()
        self.db.refresh(med)
        cache_delete(_med_list_key(patient_id), _interaction_key(patient_id))
        return med

    def list_medications(self, patient_id: str) -> List[Dict]:
        cached = cache_get(_med_list_key(patient_id))
        if cached is not None:
            logger.debug("cache hit: medications list patient=%s", patient_id)
            return cached

        today = date.today()
        rows = (
            self.db.query(Medication)
            .filter_by(patient_id=patient_id)
            .filter(
                (Medication.end_date.is_(None)) | (Medication.end_date >= today)
            )
            .order_by(Medication.created_at.desc())
            .all()
        )
        serialized = [
            {
                "id": m.id,
                "patient_id": m.patient_id,
                "medication_name": m.medication_name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "start_date": m.start_date.isoformat() if m.start_date else None,
                "end_date": m.end_date.isoformat() if m.end_date else None,
                "notes": m.notes,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            }
            for m in rows
        ]
        cache_set(_med_list_key(patient_id), serialized, ttl=_MED_LIST_TTL)
        return serialized

    def delete_medication(self, medication_id: str, patient_id: str) -> bool:
        med = self.db.query(Medication).filter_by(id=medication_id).first()
        if not med or med.patient_id != patient_id:
            return False
        self.db.delete(med)
        self.db.commit()
        cache_delete(_med_list_key(patient_id), _interaction_key(patient_id))
        return True

    def check_interactions(self, patient_id: str) -> Dict:
        cached = cache_get(_interaction_key(patient_id))
        if cached is not None:
            logger.debug("cache hit: interactions patient=%s", patient_id)
            return cached

        patient = self.db.query(Patient).filter_by(id=patient_id).first()
        meds = self.list_medications(patient_id)

        if not meds:
            return {
                "risk_level": "NONE",
                "interactions": [],
                "contraindications": [],
                "warning_signs": [],
                "patient_response": "No active medications logged.",
                "disclaimer": "",
                "confidence_score": 1.0,
            }

        med_names = [m["medication_name"] for m in meds]
        patient_info: Dict = {}
        if patient:
            patient_info = {
                "age": self._calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
                "medical_history": patient.medical_history,
                "allergies": patient.allergies,
                "current_medications": ", ".join(med_names),
            }

        try:
            result = self.agent.check_medication_interactions(med_names, patient_info)
            cache_set(_interaction_key(patient_id), result, ttl=_INTERACTION_TTL)
            return result
        except Exception as e:
            logger.error(f"Interaction check failed: {e}")
            return {
                "risk_level": "UNKNOWN",
                "interactions": [],
                "contraindications": [],
                "warning_signs": [],
                "patient_response": "Interaction check temporarily unavailable.",
                "disclaimer": "",
                "confidence_score": 0.0,
            }

    @staticmethod
    def _calculate_age(dob: date) -> int:
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
