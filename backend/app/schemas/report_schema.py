from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReportResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    text_preview: Optional[str] = None
    page_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
