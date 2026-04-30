"""Service layer for medication CRUD and interaction checking."""
import logging
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import Medication, Patient
from app.agents.medication_agent import get_medication_agent

logger = logging.getLogger(__name__)


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
        return med

    def list_medications(self, patient_id: str) -> List[Medication]:
        today = date.today()
        return (
            self.db.query(Medication)
            .filter_by(patient_id=patient_id)
            .filter(
                (Medication.end_date.is_(None)) | (Medication.end_date >= today)
            )
            .order_by(Medication.created_at.desc())
            .all()
        )

    def delete_medication(self, medication_id: str, patient_id: str) -> bool:
        med = self.db.query(Medication).filter_by(id=medication_id).first()
        if not med or med.patient_id != patient_id:
            return False
        self.db.delete(med)
        self.db.commit()
        return True

    def check_interactions(self, patient_id: str) -> Dict:
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

        med_names = [m.medication_name for m in meds]
        patient_info: Dict = {}
        if patient:
            patient_info = {
                "age": self._calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
                "medical_history": patient.medical_history,
                "allergies": patient.allergies,
                "current_medications": ", ".join(med_names),
            }

        try:
            return self.agent.check_medication_interactions(med_names, patient_info)
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
