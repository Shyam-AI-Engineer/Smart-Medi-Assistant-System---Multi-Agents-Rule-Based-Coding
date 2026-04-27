"""Patient service - profile management and vitals recording."""
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import Patient, User, Vitals
from app.schemas.patient_schema import PatientProfileUpdate, VitalsCreate

logger = logging.getLogger(__name__)


class PatientService:

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: str) -> Patient:
        """Get the patient profile for a user. Raises 404 if not found."""
        patient = self.db.query(Patient).filter_by(user_id=user_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient profile not found",
            )
        return patient

    def update(self, user_id: str, update: PatientProfileUpdate) -> Patient:
        """Partially update the patient profile. Only supplied fields are changed."""
        patient = self.get_by_user_id(user_id)
        changes = update.model_dump(exclude_unset=True)

        # Handle full_name separately (it's on User, not Patient)
        full_name = changes.pop("full_name", None)
        if full_name is not None:
            user = self.db.query(User).get(user_id)
            if user:
                user.full_name = full_name

        # Update all other fields on Patient
        for field, value in changes.items():
            setattr(patient, field, value)
        self.db.commit()
        logger.info(f"Patient profile updated: {patient.id}")
        return patient

    def add_vitals(self, user_id: str, data: VitalsCreate) -> Vitals:
        """Record a new vitals measurement for the patient."""
        patient = self.get_by_user_id(user_id)
        vitals = Vitals(
            patient_id=patient.id,
            **data.model_dump(exclude_unset=True),
        )
        self.db.add(vitals)
        self.db.commit()
        logger.info(f"Vitals recorded for patient: {patient.id}")
        return vitals

    def get_vitals(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Return paginated vitals history ordered newest-first."""
        patient = self.get_by_user_id(user_id)
        query = (
            self.db.query(Vitals)
            .filter_by(patient_id=patient.id)
            .order_by(Vitals.created_at.desc())
        )
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        }
