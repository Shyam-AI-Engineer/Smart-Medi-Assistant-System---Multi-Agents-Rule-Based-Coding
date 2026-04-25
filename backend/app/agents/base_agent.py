"""Base Agent - abstract foundation for all specialist agents."""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all medical agents."""

    def __init__(self, agent_name: str):
        """Initialize base agent with name and logging."""
        self.agent_name = agent_name
        self.logger = logger

    @abstractmethod
    def process(self, **kwargs) -> Dict[str, Any]:
        """
        Process input and return structured response.

        Returns dict with:
        - response: str (patient-friendly message)
        - agent_used: str (agent name)
        - confidence_score: float (0-1)
        - tokens_used: int (for cost tracking)
        """
        pass

    def log_decision(self, action: str, details: Dict[str, Any]) -> None:
        """Log agent decision for debugging/audit."""
        self.logger.info(
            f"{self.agent_name}.{action}",
            extra={**details, "agent": self.agent_name}
        )

    def log_error(self, action: str, error: Exception) -> None:
        """Log agent error."""
        self.logger.error(
            f"{self.agent_name}.{action}_failed",
            extra={"agent": self.agent_name, "error": str(error)},
            exc_info=True
        )

    @staticmethod
    def get_disclaimer(severity: str = "MODERATE") -> str:
        """Get appropriate medical disclaimer based on severity."""
        base = "⚠️ **DISCLAIMER**: This is not a substitute for professional medical advice."

        if severity == "CRITICAL":
            return f"{base}\n**Seek immediate medical attention or call emergency services (911).**"
        elif severity == "HIGH":
            return f"{base}\nConsult a doctor or healthcare provider immediately."
        elif severity == "MODERATE":
            return f"{base}\nConsult with your healthcare provider soon."

        return base
