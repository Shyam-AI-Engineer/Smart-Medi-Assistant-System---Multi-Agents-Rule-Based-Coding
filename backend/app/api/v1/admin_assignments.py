"""Admin doctor-patient assignment endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session, aliased

from app.extensions import get_db
from app.middleware.auth_middleware import require_role
from app.models import Patient, User
from app.models.doctor_patient_assignment import DoctorPatientAssignment
from app.utils.audit import write_audit, get_client_ip

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


class AssignmentRequest(BaseModel):
    doctor_user_id: str
    patient_id: str


@router.get("/assignments")
def list_assignments(
    doctor_user_id: Optional[str] = Query(default=None),
    patient_id: Optional[str] = Query(default=None),
    _: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """List all doctor-patient assignments, optionally filtered."""
    DoctorUser = aliased(User, name="doctor_user")
    PatientUser = aliased(User, name="patient_user")

    query = (
        db.query(DoctorPatientAssignment, DoctorUser, PatientUser)
        .join(DoctorUser, DoctorUser.id == DoctorPatientAssignment.doctor_user_id)
        .join(Patient, Patient.id == DoctorPatientAssignment.patient_id)
        .join(PatientUser, PatientUser.id == Patient.user_id)
    )
    if doctor_user_id:
        query = query.filter(DoctorPatientAssignment.doctor_user_id == doctor_user_id)
    if patient_id:
        query = query.filter(DoctorPatientAssignment.patient_id == patient_id)

    rows = query.order_by(DoctorPatientAssignment.created_at.desc()).all()
    items = [
        {
            "id": a.id,
            "doctor_user_id": a.doctor_user_id,
            "doctor_name": doc.full_name,
            "patient_id": a.patient_id,
            "patient_name": pat.full_name,
            "assigned_by": a.assigned_by,
            "created_at": a.created_at.isoformat(),
        }
        for a, doc, pat in rows
    ]
    return {"items": items, "total": len(items)}


@router.post("/assignments", status_code=201)
def create_assignment(
    body: AssignmentRequest,
    request: Request,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Assign a doctor to a patient."""
    doctor = db.query(User).filter(User.id == body.doctor_user_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor user not found")
    if doctor.role.value not in ("doctor", "admin"):
        raise HTTPException(status_code=400, detail="User is not a doctor")

    patient = db.query(Patient).filter(Patient.id == body.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing = (
        db.query(DoctorPatientAssignment)
        .filter_by(doctor_user_id=body.doctor_user_id, patient_id=body.patient_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Assignment already exists")

    assignment = DoctorPatientAssignment(
        doctor_user_id=body.doctor_user_id,
        patient_id=body.patient_id,
        assigned_by=current_user["user_id"],
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="create_assignment",
        resource_type="assignment",
        resource_id=assignment.id,
        ip_address=get_client_ip(request),
        details=f"doctor={body.doctor_user_id} patient={body.patient_id}",
    )
    return {
        "id": assignment.id,
        "doctor_user_id": assignment.doctor_user_id,
        "patient_id": assignment.patient_id,
        "assigned_by": assignment.assigned_by,
        "created_at": assignment.created_at.isoformat(),
    }


@router.delete("/assignments/{assignment_id}", status_code=200)
def delete_assignment(
    assignment_id: str,
    request: Request,
    current_user: dict = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Remove a doctor-patient assignment."""
    assignment = db.query(DoctorPatientAssignment).filter(
        DoctorPatientAssignment.id == assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    doctor_user_id = assignment.doctor_user_id
    patient_id = assignment.patient_id
    db.delete(assignment)
    db.commit()

    write_audit(
        db,
        user_id=current_user["user_id"],
        user_email=current_user["email"],
        user_role=current_user["role"],
        action="delete_assignment",
        resource_type="assignment",
        resource_id=assignment_id,
        ip_address=get_client_ip(request),
        details=f"doctor={doctor_user_id} patient={patient_id}",
    )
    return {"deleted": True, "id": assignment_id}
