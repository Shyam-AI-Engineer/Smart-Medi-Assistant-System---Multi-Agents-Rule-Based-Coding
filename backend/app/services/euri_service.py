"""Euri API service - OpenAI-compatible client for embeddings and LLM generation.

Euri base URL: https://api.euron.one/api/v1/euri
Embedding model: gemini-embedding-2-preview (768 dimensions)
LLM model: gpt-4o-mini
"""
import json
import os
import logging
from typing import Any, Dict, List, Optional

import httpx
from openai import OpenAI, APIError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.euri_prompts import (
    build_medical_system_prompt,
    build_rag_message,
    build_triage_system_prompt,
    build_triage_message,
)

logger = logging.getLogger(__name__)

_ORCHESTRATOR_SYSTEM = """You are the orchestrator agent for a medical AI assistant.
Analyze patient messages and route them to the correct specialist agent.

Available agents:
- clinical: Medical knowledge, symptom analysis, differential diagnosis
- rag: Medical document/literature retrieval and analysis
- medication: Drug interactions, contraindications, warnings
- triage: Urgency assessment, emergency detection

Respond with ONLY valid JSON:
{
    "routing_intent": "clinical|rag|medication|triage",
    "confidence": 0.0-1.0,
    "reason": "Why you chose this routing",
    "agent_to_call": "agent_name"
}"""

_TRIAGE_FALLBACK = {
    "urgency_level": "urgent", "severity_score": 7,
    "escalation_path": "Urgent Care",
    "immediate_action": "Please seek medical attention from a healthcare provider",
    "warning_signs": [], "reasoning": "Unable to complete assessment",
    "next_steps": ["Contact healthcare provider"], "confidence_score": 0.0,
}


class EuriService:
    def __init__(self):
        self.api_key = os.getenv("EURI_API_KEY")
        self.base_url = os.getenv("EURI_BASE_URL", "https://api.euron.one/api/v1/euri")
        self.embedding_model = os.getenv("EURI_EMBEDDING_MODEL", "gemini-embedding-2-preview")
        self.llm_model = os.getenv("EURI_LLM_MODEL", "gpt-4o-mini")
        self.embedding_dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))
        self.client: Optional[OpenAI] = None
        self._initialized = False
        self._init_error: Optional[str] = None

        if not self.api_key:
            self._init_error = "EURI_API_KEY not set in environment"
            logger.warning(self._init_error)

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return self.client is not None
        if self._init_error:
            self._initialized = True
            return False
        try:
            import certifi
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=30.0,
                http_client=httpx.Client(verify=certifi.where()),
            )
            self._initialized = True
            return True
        except Exception as e:
            self._init_error = str(e)
            self._initialized = True
            logger.error(f"Failed to initialize Euri client: {e}")
            return False

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_text(self, text: str, dimensions: Optional[int] = None) -> List[float]:
        if not self._ensure_initialized():
            raise RuntimeError("Euri service not initialized")
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                dimensions=dimensions or self.embedding_dimensions,
            )
            return response.data[0].embedding
        except APIError as e:
            logger.error(f"Euri embedding failed: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def embed_medical_content(
        self, content: str, content_type: str = "text", source_name: Optional[str] = None
    ) -> Dict[str, Any]:
        if len(content) > 32000:
            logger.warning(f"Content too long ({len(content)} chars), truncating")
            content = content[:32000]
        embedding = self.embed_text(content)
        return {
            "embedding": embedding,
            "dimensions": self.embedding_dimensions,
            "source_type": content_type,
            "source_name": source_name or "unknown",
            "content_preview": content[:200],
            "tokens_used": len(content) // 4,
        }

    # ------------------------------------------------------------------
    # LLM generation
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_medical_response(
        self,
        patient_question: str,
        medical_context: str,
        patient_info: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> str:
        if not self._ensure_initialized():
            raise RuntimeError("Euri service not initialized")
        response = self.client.chat.completions.create(
            model=self.llm_model,
            messages=[
                {"role": "system", "content": build_medical_system_prompt(patient_info)},
                {"role": "user", "content": build_rag_message(patient_question, medical_context, patient_info)},
            ],
            temperature=0.3,
            max_tokens=2048,
            stream=stream,
        )
        if stream:
            return response
        return response.choices[0].message.content

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_orchestrator_response(
        self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        if not self._ensure_initialized():
            return {"routing_intent": "clinical", "confidence": 0.5,
                    "reason": "Fallback - Euri unavailable", "agent_to_call": "clinical_agent"}
        history_ctx = ""
        if chat_history:
            history_ctx = "\nChat history:\n" + "".join(
                f"- {m['role']}: {m['content'][:100]}\n" for m in chat_history[-3:]
            )
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": _ORCHESTRATOR_SYSTEM},
                    {"role": "user", "content": f"Patient message: {user_message}{history_ctx}"},
                ],
                temperature=0.3,
                max_tokens=256,
            )
            return json.loads(response.choices[0].message.content)
        except (APIError, json.JSONDecodeError) as e:
            logger.error(f"Orchestrator routing failed: {e}")
            return {"routing_intent": "clinical", "confidence": 0.5,
                    "reason": "Fallback due to API error", "agent_to_call": "clinical_agent"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_triage_assessment(
        self,
        patient_message: str,
        patient_info: Optional[Dict[str, Any]] = None,
        assessment_type: str = "general",
    ) -> Dict[str, Any]:
        if not self._ensure_initialized():
            return _TRIAGE_FALLBACK
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": build_triage_system_prompt(assessment_type)},
                    {"role": "user", "content": build_triage_message(patient_message, patient_info, assessment_type)},
                ],
                temperature=0.2,
                max_tokens=512,
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "urgency_level": result.get("urgency_level", "moderate"),
                "severity_score": int(result.get("severity_score", 5)),
                "escalation_path": result.get("escalation_path", "Doctor Visit"),
                "immediate_action": result.get("immediate_action", "Contact healthcare provider"),
                "warning_signs": result.get("warning_signs", []),
                "reasoning": result.get("reasoning", ""),
                "next_steps": result.get("next_steps", []),
                "confidence_score": float(result.get("confidence_score", 0.8)),
            }
        except (APIError, json.JSONDecodeError) as e:
            logger.error(f"Triage assessment failed: {e}")
            return _TRIAGE_FALLBACK

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "status": "unknown", "embedding_api": False,
            "llm_api": False, "base_url": self.base_url, "error": None,
        }
        if not self._ensure_initialized():
            result["status"] = "unavailable"
            result["error"] = self._init_error or "Euri service not configured"
            return result

        try:
            resp = self.client.embeddings.create(
                model=self.embedding_model, input="Health check", dimensions=self.embedding_dimensions
            )
            result["embedding_api"] = len(resp.data[0].embedding) == self.embedding_dimensions
        except Exception as e:
            result["error"] = f"Embeddings API failed: {e}"

        try:
            resp = self.client.chat.completions.create(
                model=self.llm_model, messages=[{"role": "user", "content": "Hi"}], max_tokens=10
            )
            result["llm_api"] = bool(resp.choices[0].message.content)
        except Exception as e:
            result["error"] = f"LLM API failed: {e}"

        if result["embedding_api"] and result["llm_api"]:
            result["status"] = "healthy"
        elif result["embedding_api"] or result["llm_api"]:
            result["status"] = "degraded"
        else:
            result["status"] = "unavailable"
        return result


_euri_service: Optional[EuriService] = None


def get_euri_service() -> EuriService:
    global _euri_service
    if _euri_service is None:
        _euri_service = EuriService()
    return _euri_service
