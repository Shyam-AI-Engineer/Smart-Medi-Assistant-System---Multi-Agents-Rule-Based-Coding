"""Pure text-extraction helpers for the chat pipeline."""
import re
from typing import Dict, List


def extract_medications(message: str) -> List[str]:
    """Return known medication names found in the message (lowercase match)."""
    known_meds = [
        "ibuprofen", "aspirin", "paracetamol", "acetaminophen",
        "metformin", "lisinopril", "warfarin", "metoprolol",
        "amlodipine", "clopidogrel", "diltiazem", "verapamil",
        "alcohol", "contrast dye", "potassium",
    ]
    msg_lower = message.lower()
    return [med for med in known_meds if med in msg_lower]


def extract_vitals_from_message(message: str) -> Dict[str, float]:
    """Parse vital sign values from free-text (heart rate, BP, temp, O2, RR)."""
    vitals: Dict[str, float] = {}
    msg = message.lower()

    for pattern in (r"heart\s+rate[:\s]+(\d+)", r"pulse[:\s]+(\d+)", r"hr[:\s]+(\d+)"):
        m = re.search(pattern, msg)
        if m:
            vitals["heart_rate"] = float(m.group(1))
            break

    for pattern in (
        r"(?:blood\s+)?pressure[:\s]+(\d+)\s*[/\\]\s*(\d+)",
        r"bp[:\s]+(\d+)\s*[/\\]\s*(\d+)",
    ):
        m = re.search(pattern, msg)
        if m:
            vitals["blood_pressure_systolic"] = float(m.group(1))
            vitals["blood_pressure_diastolic"] = float(m.group(2))
            break

    for pattern in (r"temperature[:\s]+(\d+\.?\d*)", r"temp[:\s]+(\d+\.?\d*)", r"fever[:\s]+(\d+\.?\d*)"):
        m = re.search(pattern, msg)
        if m:
            vitals["temperature"] = float(m.group(1))
            break

    for pattern in (r"(?:oxygen|spo2)[:\s]+(\d+)", r"o2[:\s]+(\d+)"):
        m = re.search(pattern, msg)
        if m:
            vitals["oxygen_saturation"] = float(m.group(1))
            break

    for pattern in (r"respiratory\s+rate[:\s]+(\d+)", r"breathing\s+rate[:\s]+(\d+)"):
        m = re.search(pattern, msg)
        if m:
            vitals["respiratory_rate"] = float(m.group(1))
            break

    return vitals
