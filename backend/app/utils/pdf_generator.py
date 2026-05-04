"""PDF generation utilities for patient vitals and doctor summaries."""
import io
from datetime import datetime
from typing import List, Optional, Dict, Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

# ── Colour palette ────────────────────────────────────────────────────────────
BRAND_BLUE = colors.HexColor("#1E86EE")
DARK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6B7280")
LIGHT_BG = colors.HexColor("#F9FAFB")
BORDER = colors.HexColor("#E5E7EB")
RED = colors.HexColor("#EF4444")
GREEN = colors.HexColor("#10B981")
YELLOW = colors.HexColor("#F59E0B")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _base_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("AppTitle", parent=styles["Title"],
                              fontSize=20, textColor=BRAND_BLUE,
                              spaceAfter=2, leading=24))
    styles.add(ParagraphStyle("AppSubtitle", parent=styles["Normal"],
                              fontSize=10, textColor=MUTED, spaceAfter=0))
    styles.add(ParagraphStyle("SectionHead", parent=styles["Heading2"],
                              fontSize=12, textColor=DARK,
                              spaceBefore=14, spaceAfter=4, leading=16))
    styles.add(ParagraphStyle("FieldLabel", parent=styles["Normal"],
                              fontSize=8, textColor=MUTED,
                              spaceAfter=1, leading=10))
    styles.add(ParagraphStyle("FieldValue", parent=styles["Normal"],
                              fontSize=10, textColor=DARK,
                              spaceAfter=6, leading=13))
    styles.add(ParagraphStyle("Disclaimer", parent=styles["Normal"],
                              fontSize=8, textColor=MUTED,
                              leading=11, spaceAfter=0))
    styles.add(ParagraphStyle("Right", parent=styles["Normal"],
                              fontSize=8, textColor=MUTED, alignment=TA_RIGHT))
    return styles


def _header(story, styles, title: str, subtitle: str, generated_by: str) -> None:
    story.append(Paragraph("Smart Medi Assistant", styles["AppTitle"]))
    story.append(Paragraph(subtitle, styles["AppSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')} &nbsp;&nbsp;|&nbsp;&nbsp; By: {generated_by}",
        styles["Right"],
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(title, styles["SectionHead"]))


def _disclaimer(story, styles) -> None:
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=6))
    story.append(Paragraph(
        "<b>Disclaimer:</b> This report is for informational purposes only and does not "
        "constitute medical advice. Please consult a licensed healthcare professional for "
        "diagnosis and treatment decisions.",
        styles["Disclaimer"],
    ))


def _anomaly_colour(anomaly: bool) -> colors.Color:
    return RED if anomaly else GREEN


def _vitals_table(vitals: List[Dict[str, Any]]) -> Table:
    headers = ["Date / Time", "HR\n(bpm)", "BP\n(mmHg)", "SpO₂\n(%)", "Temp\n(°C)",
               "Weight\n(kg)", "RR\n(/min)", "Status"]
    rows = [headers]
    for v in vitals:
        hr = str(v.get("heart_rate") or "—")
        sys_bp = v.get("blood_pressure_systolic")
        dia_bp = v.get("blood_pressure_diastolic")
        bp = f"{sys_bp}/{dia_bp}" if sys_bp and dia_bp else "—"
        spo2 = str(v.get("oxygen_saturation") or "—")
        temp = f"{v['temperature']:.1f}" if v.get("temperature") is not None else "—"
        weight = str(v.get("weight") or "—")
        rr = str(v.get("respiratory_rate") or "—")
        anomaly = v.get("anomaly_detected", False)
        status = "⚠ Flagged" if anomaly else "Normal"

        ts = v.get("created_at", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts = dt.strftime("%b %d, %Y\n%H:%M UTC")
        except Exception:
            pass

        rows.append([ts, hr, bp, spo2, temp, weight, rr, status])

    col_widths = [38 * mm, 15 * mm, 22 * mm, 15 * mm, 16 * mm, 18 * mm, 15 * mm, 20 * mm]

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    # Colour "Flagged" rows
    for i, v in enumerate(vitals, start=1):
        if v.get("anomaly_detected"):
            style.append(("TEXTCOLOR", (7, i), (7, i), RED))
            style.append(("FONTNAME", (7, i), (7, i), "Helvetica-Bold"))

    tbl.setStyle(TableStyle(style))
    return tbl


# ── Public API ────────────────────────────────────────────────────────────────

def generate_patient_vitals_pdf(
    *,
    patient_name: str,
    patient_email: str,
    date_of_birth: Optional[str],
    allergies: Optional[str],
    current_medications: Optional[str],
    vitals: List[Dict[str, Any]],
) -> io.BytesIO:
    """
    Generate a PDF vitals report for the patient to bring to their doctor.

    Returns a BytesIO with the PDF bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    styles = _base_styles()
    story = []

    _header(
        story, styles,
        title=f"Vitals History Report — {patient_name}",
        subtitle="Patient Health Summary",
        generated_by=patient_name,
    )

    # Patient info strip
    info_data = [
        [
            Paragraph("<b>Patient</b>", styles["FieldLabel"]),
            Paragraph("<b>Email</b>", styles["FieldLabel"]),
            Paragraph("<b>Date of Birth</b>", styles["FieldLabel"]),
        ],
        [
            Paragraph(patient_name, styles["FieldValue"]),
            Paragraph(patient_email, styles["FieldValue"]),
            Paragraph(date_of_birth or "Not provided", styles["FieldValue"]),
        ],
    ]
    info_tbl = Table(info_data, colWidths=[(PAGE_W - 2 * MARGIN) / 3] * 3)
    info_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 6))

    # Allergies / medications
    if allergies or current_medications:
        med_data = []
        if allergies:
            med_data.append([
                Paragraph("<b>Allergies</b>", styles["FieldLabel"]),
                Paragraph(allergies, styles["FieldValue"]),
            ])
        if current_medications:
            med_data.append([
                Paragraph("<b>Current Medications</b>", styles["FieldLabel"]),
                Paragraph(current_medications, styles["FieldValue"]),
            ])
        w = PAGE_W - 2 * MARGIN
        med_tbl = Table(med_data, colWidths=[40 * mm, w - 40 * mm])
        med_tbl.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(med_tbl)
        story.append(Spacer(1, 4))

    # Vitals section
    story.append(Paragraph(f"Vitals History ({len(vitals)} records)", styles["SectionHead"]))
    if not vitals:
        story.append(Paragraph("No vitals recorded yet.", styles["FieldValue"]))
    else:
        story.append(_vitals_table(vitals))

    _disclaimer(story, styles)
    doc.build(story)
    buf.seek(0)
    return buf


def generate_doctor_patient_summary_pdf(
    *,
    patient_name: str,
    patient_email: str,
    date_of_birth: Optional[str],
    allergies: Optional[str],
    current_medications: Optional[str],
    medical_history: Optional[str],
    emergency_contact: Optional[str],
    vitals: List[Dict[str, Any]],
    summary: Dict[str, Any],
    doctor_name: str,
) -> io.BytesIO:
    """
    Generate a comprehensive patient summary PDF for the doctor.

    Returns a BytesIO with the PDF bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
    )
    styles = _base_styles()
    story = []

    _header(
        story, styles,
        title=f"Patient Summary — {patient_name}",
        subtitle="Doctor Dashboard Export",
        generated_by=f"Dr. {doctor_name}",
    )

    # Summary status row
    latest_status = summary.get("latest_status", "UNKNOWN")
    risk_level = summary.get("risk_level", "UNKNOWN")
    total_messages = summary.get("total_messages", 0)
    latest_vital_at = summary.get("latest_vital_at") or "—"
    try:
        dt = datetime.fromisoformat(latest_vital_at.replace("Z", "+00:00"))
        latest_vital_at = dt.strftime("%b %d, %Y %H:%M UTC")
    except Exception:
        pass

    status_data = [
        ["Latest Status", "Risk Level", "AI Messages", "Last Reading"],
        [latest_status, risk_level, str(total_messages), latest_vital_at],
    ]
    status_tbl = Table(status_data, colWidths=[(PAGE_W - 2 * MARGIN) / 4] * 4)

    def _status_colour(val: str) -> colors.Color:
        return {
            "CRITICAL": RED, "HIGH": YELLOW, "MODERATE": BRAND_BLUE,
            "NORMAL": GREEN, "LOW": GREEN,
        }.get(val, MUTED)

    status_style = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("TEXTCOLOR", (0, 1), (0, 1), _status_colour(latest_status)),
        ("TEXTCOLOR", (1, 1), (1, 1), _status_colour(risk_level)),
        ("FONTNAME", (0, 1), (1, 1), "Helvetica-Bold"),
    ]
    status_tbl.setStyle(TableStyle(status_style))
    story.append(status_tbl)
    story.append(Spacer(1, 8))

    # Medical info
    story.append(Paragraph("Patient Information", styles["SectionHead"]))
    fields = [
        ("Full Name", patient_name),
        ("Email", patient_email),
        ("Date of Birth", date_of_birth or "Not provided"),
        ("Allergies", allergies or "None reported"),
        ("Current Medications", current_medications or "None reported"),
        ("Medical History", medical_history or "No history recorded"),
        ("Emergency Contact", emergency_contact or "Not provided"),
    ]
    w = PAGE_W - 2 * MARGIN
    field_data = [
        [Paragraph(f"<b>{k}</b>", styles["FieldLabel"]), Paragraph(v, styles["FieldValue"])]
        for k, v in fields
    ]
    field_tbl = Table(field_data, colWidths=[40 * mm, w - 40 * mm])
    field_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [LIGHT_BG, colors.white]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(field_tbl)

    # Vitals history
    story.append(Paragraph(f"Vitals History ({len(vitals)} records)", styles["SectionHead"]))
    if not vitals:
        story.append(Paragraph("No vitals recorded yet.", styles["FieldValue"]))
    else:
        story.append(_vitals_table(vitals))

    _disclaimer(story, styles)
    doc.build(story)
    buf.seek(0)
    return buf
