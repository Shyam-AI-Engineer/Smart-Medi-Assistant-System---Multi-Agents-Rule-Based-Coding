"""Reports API endpoint.

Routes:
  POST /api/v1/reports/upload  – upload and ingest a medical report
  GET /api/v1/reports/         – list patient's reports
  DELETE /api/v1/reports/{id}  – delete a report
"""

import logging
from io import BytesIO
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
    status,
)
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models import Patient, MedicalReport, ReportStatus
from app.schemas.report_schema import ReportResponse, ReportListResponse
from app.middleware.auth_middleware import get_current_user
from app.middleware.rate_limit import limiter
from app.extensions import get_db
from app.agents.clinical_agent import get_clinical_agent
from app.services.faiss_service import get_faiss_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


def _extract_text_from_pdf(content: bytes) -> tuple[str, int]:
    """Extract text from PDF. Returns (text, page_count)."""
    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(BytesIO(content))
        page_count = len(reader.pages)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip(), page_count
    except Exception as e:
        raise ValueError(f"Failed to extract PDF: {e}")


def _extract_text_from_docx(content: bytes) -> tuple[str, int]:
    """Extract text from DOCX. Returns (text, page_count=None)."""
    try:
        from docx import Document

        doc = Document(BytesIO(content))
        text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return text.strip(), None
    except Exception as e:
        raise ValueError(f"Failed to extract DOCX: {e}")


def _extract_text_from_txt(content: bytes) -> tuple[str, int]:
    """Extract text from TXT. Returns (text, page_count=None)."""
    try:
        text = content.decode("utf-8")
        return text.strip(), None
    except Exception as e:
        raise ValueError(f"Failed to decode TXT: {e}")


@router.post(
    "/upload",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
async def upload_report(
    request: Request,  # Required by rate limiter decorator
    file: UploadFile = File(..., description="PDF, DOCX, or TXT file (max 10 MB)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportResponse:
    """
    Upload a medical report (lab result, discharge summary, etc).

    Supported formats: PDF, DOCX, TXT
    Maximum file size: 10 MB

    The report is automatically ingested into the medical knowledge base
    so the AI can reference it in future questions.
    """
    # Get patient
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    # Validate filename and size
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Get file extension
    filename_lower = file.filename.lower()
    ext = None
    file_type = None

    for allowed_ext in ALLOWED_EXTENSIONS:
        if filename_lower.endswith(allowed_ext):
            ext = allowed_ext
            file_type = allowed_ext.lstrip(".")
            break

    if not ext:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {MAX_FILE_BYTES // 1024 // 1024} MB)",
        )

    # Create report record (status=PROCESSING)
    report = MedicalReport(
        patient_id=patient.id,
        filename=file.filename,
        file_type=file_type,
        status=ReportStatus.PROCESSING,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Extract text
    try:
        if ext == ".pdf":
            text, page_count = _extract_text_from_pdf(content)
        elif ext == ".docx":
            text, page_count = _extract_text_from_docx(content)
        else:  # .txt
            text, page_count = _extract_text_from_txt(content)

        if not text:
            raise ValueError("Extracted text is empty")

        # Ingest into FAISS via clinical agent
        agent = get_clinical_agent()
        ingest_result = agent.ingest_medical_document(
            content=text,
            source_type=file_type,
            source_name=file.filename,
            metadata={"patient_id": patient.id, "report_db_id": report.id},
        )

        if not ingest_result.get("success"):
            raise ValueError(ingest_result.get("message", "Ingestion failed"))

        # Update report: status=DONE
        report.status = ReportStatus.DONE
        report.faiss_doc_id = ingest_result.get("document_id")
        report.text_preview = text[:300]
        report.page_count = page_count
        db.commit()
        db.refresh(report)

        logger.info(
            f"Report uploaded",
            extra={
                "patient_id": patient.id,
                "report_id": report.id,
                "report_filename": file.filename,
            },
        )

    except Exception as e:
        # Update report: status=ERROR
        report.status = ReportStatus.ERROR
        report.error_message = str(e)
        db.commit()

        logger.error(
            f"Failed to ingest report: {e}",
            extra={"patient_id": patient.id, "report_id": report.id},
        )

    return ReportResponse.model_validate(report)


@router.get("/", response_model=ReportListResponse)
def list_reports(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ReportListResponse:
    """List all medical reports for the authenticated patient."""
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    reports = (
        db.query(MedicalReport)
        .filter_by(patient_id=patient.id)
        .order_by(desc(MedicalReport.created_at))
        .all()
    )

    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports], total=len(reports)
    )


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
def delete_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Delete a medical report and remove from knowledge base."""
    patient = db.query(Patient).filter_by(user_id=current_user["user_id"]).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    report = db.query(MedicalReport).filter_by(id=report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Verify ownership
    if report.patient_id != patient.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Remove from FAISS if ingested
    if report.faiss_doc_id:
        try:
            faiss_service = get_faiss_service()
            faiss_service.delete_document(report.faiss_doc_id)
        except Exception as e:
            logger.error(f"Failed to delete FAISS document: {e}")

    # Delete from database
    db.delete(report)
    db.commit()

    logger.info(f"Report deleted: {report_id}")

    return {"success": True}
