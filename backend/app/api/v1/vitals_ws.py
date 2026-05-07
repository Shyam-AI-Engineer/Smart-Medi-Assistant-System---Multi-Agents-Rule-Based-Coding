"""Vitals WebSocket and PDF export endpoints."""
import json
import logging
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import get_current_user
from app.extensions import get_db
from app.agents.monitoring_agent import get_monitoring_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vitals", tags=["vitals"])


@router.get("/{patient_id}/export", status_code=status.HTTP_200_OK, summary="Export vitals as PDF")
def export_vitals_pdf(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Generate and download a PDF vitals report for the patient."""
    from app.models import Patient, User
    from app.models.vitals import Vitals
    from app.utils.pdf_generator import generate_patient_vitals_pdf

    if current_user["role"] == "patient":
        own_patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
        if not own_patient or own_patient.id != patient_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        patient = own_patient
    else:
        patient = db.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")

    user = db.query(User).filter_by(id=patient.user_id).first()
    patient_name = (user.full_name if user else None) or "Unknown"
    patient_email = (user.email if user else None) or ""

    vitals_qs = (
        db.query(Vitals)
        .filter_by(patient_id=patient_id)
        .order_by(Vitals.created_at.desc())
        .limit(100)
        .all()
    )
    vitals_data = [
        {
            "heart_rate": v.heart_rate,
            "blood_pressure_systolic": v.blood_pressure_systolic,
            "blood_pressure_diastolic": v.blood_pressure_diastolic,
            "temperature": v.temperature,
            "oxygen_saturation": v.oxygen_saturation,
            "weight": v.weight,
            "respiratory_rate": getattr(v, "respiratory_rate", None),
            "anomaly_detected": v.anomaly_detected,
            "created_at": v.created_at.isoformat() if v.created_at else "",
        }
        for v in vitals_qs
    ]

    dob = patient.date_of_birth.isoformat() if patient.date_of_birth else None
    pdf_buf = generate_patient_vitals_pdf(
        patient_name=patient_name,
        patient_email=patient_email,
        date_of_birth=dob,
        allergies=patient.allergies,
        current_medications=patient.current_medications,
        vitals=vitals_data,
    )
    filename = f"vitals_{patient_name.replace(' ', '_')}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.websocket("/ws/{patient_id}")
async def websocket_vitals(websocket: WebSocket, patient_id: str):
    """Real-time vitals streaming and analysis via WebSocket."""
    try:
        await websocket.accept()
        logger.info(f"WebSocket connected for patient {patient_id}")

        while True:
            data = await websocket.receive_text()
            try:
                vitals_data = json.loads(data)
                vitals: Dict[str, float] = {}
                for field in ("heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic",
                              "temperature", "oxygen_saturation", "respiratory_rate"):
                    if vitals_data.get(field) is not None:
                        vitals[field] = float(vitals_data[field])

                if not vitals:
                    await websocket.send_json({"status": "error", "message": "No vital measurements provided"})
                    continue

                analysis = get_monitoring_agent().analyze_vitals(vitals=vitals, patient_info=None)
                await websocket.send_json({
                    "status": "success",
                    "vitals": vitals,
                    "analysis": analysis,
                    "timestamp": analysis.get("timestamp"),
                })

            except json.JSONDecodeError:
                await websocket.send_json({"status": "error", "message": "Invalid JSON format"})
            except ValueError as e:
                await websocket.send_json({"status": "error", "message": f"Invalid vital value: {e}"})
            except Exception as e:
                logger.error(f"WebSocket analysis error: {e}")
                await websocket.send_json({"status": "error", "message": "Failed to analyze vitals"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for patient {patient_id}")
    except Exception as e:
        logger.error(f"WebSocket error for patient {patient_id}: {e}")
        try:
            await websocket.close(code=status.WS_1011_SERVER_ERROR)
        except (RuntimeError, OSError):
            pass
