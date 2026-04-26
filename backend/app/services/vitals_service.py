"""Vitals service — store measurements, analyze via MonitoringAgent, compute trend."""
import logging
from typing import Dict, Any, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Patient, Vitals
from app.agents.monitoring_agent import get_monitoring_agent
from app.schemas.vitals_schema import VitalsStoreRequest, TrendEnum

logger = logging.getLogger(__name__)

# Thresholds for trend evaluation (same direction as VITAL_THRESHOLDS in agent)
_WORSENING_DIRECTION = {
    "heart_rate": "increasing",       # high HR is bad
    "blood_pressure_systolic": "increasing",
    "blood_pressure_diastolic": "increasing",
    "oxygen_saturation": "decreasing",  # low SpO2 is bad
    "temperature": "increasing",
    "respiratory_rate": "increasing",
}

# Minimum relative change required to count as a trend signal (per metric)
_CHANGE_THRESHOLDS = {
    "heart_rate": 0.08,               # 8% change
    "blood_pressure_systolic": 0.05,
    "blood_pressure_diastolic": 0.05,
    "oxygen_saturation": 0.02,        # 2% absolute change is meaningful for SpO2
    "temperature": 0.015,             # ~0.5°C on a 37°C baseline
    "respiratory_rate": 0.10,
}


class VitalsService:
    """Handles vitals storage, AI analysis, and trend detection."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------ #
    # Public methods                                                       #
    # ------------------------------------------------------------------ #

    def store_and_analyze(
        self,
        request: VitalsStoreRequest,
        current_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Persist vitals, run MonitoringAgent analysis, and compute trend.

        Access control:
        - patient role: patient_id must match their own profile
        - doctor / admin: any patient_id is allowed
        """
        patient = self._get_patient_with_access_check(
            request.patient_id, current_user
        )

        # Build vitals dict for MonitoringAgent (exclude storage-only fields)
        vitals_for_analysis: Dict[str, float] = {}
        for field in (
            "heart_rate",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "oxygen_saturation",
            "temperature",
            "respiratory_rate",
        ):
            value = getattr(request, field)
            if value is not None:
                vitals_for_analysis[field] = value

        if not vitals_for_analysis:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one vital sign measurement is required",
            )

        # Fetch recent history for trend analysis (before saving new record)
        recent_records = self._get_recent_records(patient.id, limit=5)

        # Persist new record
        anomaly = False
        record = self._save_vitals(patient.id, request, anomaly)

        # Analyse with MonitoringAgent
        agent = get_monitoring_agent()
        analysis = agent.analyze_vitals(vitals=vitals_for_analysis)

        # Update anomaly flag based on analysis result
        if analysis.get("overall_status") in ("HIGH", "CRITICAL"):
            record.anomaly_detected = True
            record.anomaly_score = analysis.get("confidence_score", 0.0)
            self.db.commit()

        # Compute trend from historical records
        trend = self._compute_trend(recent_records, vitals_for_analysis)

        logger.info(
            f"Vitals stored and analysed for patient {patient.id}: "
            f"status={analysis.get('overall_status')}, trend={trend}"
        )

        return {"record": record, "analysis": analysis, "trend": trend}

    def get_history(
        self,
        patient_id: str,
        current_user: Dict[str, Any],
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Return paginated vitals history (newest first)."""
        patient = self._get_patient_with_access_check(patient_id, current_user)

        query = (
            self.db.query(Vitals)
            .filter_by(patient_id=patient.id)
            .order_by(Vitals.created_at.desc())
        )
        total = query.count()
        items = query.offset(offset).limit(limit).all()

        return {
            "patient_id": patient.id,
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        }

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _get_patient_with_access_check(
        self,
        patient_id: str,
        current_user: Dict[str, Any],
    ) -> Patient:
        """Fetch patient and enforce role-based access control."""
        patient = self.db.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {patient_id} not found",
            )

        role = current_user.get("role")
        if role == "patient":
            # Patients may only access their own records
            own = self.db.query(Patient).filter_by(
                user_id=current_user["user_id"]
            ).first()
            if not own or own.id != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Patients may only access their own vitals",
                )

        return patient

    def _save_vitals(
        self,
        patient_id: str,
        request: VitalsStoreRequest,
        anomaly_detected: bool,
    ) -> Vitals:
        """Create and persist a Vitals row."""
        record = Vitals(
            patient_id=patient_id,
            heart_rate=int(request.heart_rate) if request.heart_rate is not None else None,
            blood_pressure_systolic=int(request.blood_pressure_systolic) if request.blood_pressure_systolic is not None else None,
            blood_pressure_diastolic=int(request.blood_pressure_diastolic) if request.blood_pressure_diastolic is not None else None,
            temperature=request.temperature,
            oxygen_saturation=request.oxygen_saturation,
            weight=request.weight,
            notes=request.notes,
            anomaly_detected=anomaly_detected,
        )
        self.db.add(record)
        self.db.commit()
        return record

    def _get_recent_records(self, patient_id: str, limit: int = 5) -> List[Vitals]:
        """Fetch the most recent vitals records (newest first)."""
        return (
            self.db.query(Vitals)
            .filter_by(patient_id=patient_id)
            .order_by(Vitals.created_at.desc())
            .limit(limit)
            .all()
        )

    def _compute_trend(
        self,
        previous_records: List[Vitals],
        latest_values: Dict[str, float],
    ) -> str:
        """
        Compare latest vitals against recent history to detect WORSENING /
        IMPROVING / STABLE.

        Strategy:
        - For each metric present in both latest and history, compute the
          percentage change from the rolling average.
        - Count how many metrics are worsening vs improving.
        - Majority wins; tie → STABLE.
        - If there is no history, return STABLE (insufficient data).
        """
        if not previous_records:
            return TrendEnum.STABLE

        worsening = 0
        improving = 0

        for metric, direction in _WORSENING_DIRECTION.items():
            latest_val = latest_values.get(metric)
            if latest_val is None:
                continue

            # Build list of previous non-null values for this metric
            prev_values: List[float] = []
            for rec in previous_records:
                val = getattr(rec, metric, None)
                if val is not None:
                    prev_values.append(float(val))

            if not prev_values:
                continue

            prev_avg = sum(prev_values) / len(prev_values)
            if prev_avg == 0:
                continue

            threshold = _CHANGE_THRESHOLDS.get(metric, 0.05)
            relative_change = (latest_val - prev_avg) / abs(prev_avg)

            if direction == "increasing":
                # Metric worsens as it rises
                if relative_change > threshold:
                    worsening += 1
                elif relative_change < -threshold:
                    improving += 1
            else:
                # direction == "decreasing": metric worsens as it falls
                if relative_change < -threshold:
                    worsening += 1
                elif relative_change > threshold:
                    improving += 1

        if worsening > improving:
            return TrendEnum.WORSENING
        if improving > worsening:
            return TrendEnum.IMPROVING
        return TrendEnum.STABLE
