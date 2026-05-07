"""Chat history persistence — save, retrieve, and feedback for chat records."""
import logging
from datetime import datetime
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.models import ChatHistory

logger = logging.getLogger(__name__)


class ChatHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def save(self, patient_id: str, user_message: str, agent_response: Dict[str, Any]) -> bool:
        """Persist a chat exchange to the database."""
        try:
            chat = ChatHistory(
                patient_id=patient_id,
                user_message=user_message,
                ai_response=agent_response.get("response", ""),
                agent_used=agent_response.get("agent_used", "unknown"),
                confidence_score=agent_response.get("confidence_score", 0.5),
                tokens_used=agent_response.get("tokens_used", 0),
            )
            self.db.add(chat)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")
            self.db.rollback()
            return False

    def submit_feedback(self, chat_id: str, patient_id: str, feedback: str) -> bool:
        """Record thumbs_up/thumbs_down feedback on a chat message."""
        try:
            chat = self.db.query(ChatHistory).filter_by(id=chat_id, patient_id=patient_id).first()
            if not chat:
                return False
            chat.feedback = feedback
            chat.feedback_at = datetime.utcnow()
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
            self.db.rollback()
            return False

    def get_history(self, patient_id: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Paginated chat history for a patient, newest first."""
        try:
            query = (
                self.db.query(ChatHistory)
                .filter_by(patient_id=patient_id)
                .order_by(ChatHistory.created_at.desc())
            )
            total = query.count()
            items = query.offset(offset).limit(limit).all()
            return {
                "items": [
                    {
                        "id": c.id,
                        "user_message": c.user_message,
                        "ai_response": c.ai_response,
                        "agent_used": c.agent_used,
                        "confidence_score": c.confidence_score,
                        "feedback": c.feedback,
                        "created_at": c.created_at.isoformat(),
                    }
                    for c in items
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_next": offset + limit < total,
            }
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return {"items": [], "total": 0, "limit": limit, "offset": offset, "has_next": False}
