"""Euri API service - unified embeddings + LLM provider.

Euri (https://api.euron.one/api/v1/euri) is OpenAI-compatible and provides:
- Embeddings: gemini-embedding-2-preview (768 dimensions)
- LLM: gpt-4o-mini (medical-optimized)

Single API key for both services. Custom base_url overrides OpenAI defaults.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI, APIError
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class EuriService:
    """Unified Euri API client for embeddings and LLM generation."""

    def __init__(self):
        """Initialize Euri client with OpenAI SDK."""
        self.api_key = os.getenv("EURI_API_KEY")
        self.base_url = os.getenv(
            "EURI_BASE_URL",
            "https://api.euron.one/api/v1/euri"
        )
        self.embedding_model = os.getenv(
            "EURI_EMBEDDING_MODEL",
            "gemini-embedding-2-preview"
        )
        self.llm_model = os.getenv(
            "EURI_LLM_MODEL",
            "gpt-4o-mini"
        )
        self.embedding_dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))

        if not self.api_key:
            raise ValueError("EURI_API_KEY not set in environment")

        # Single client for both embeddings and LLM
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_text(
        self,
        text: str,
        dimensions: Optional[int] = None,
    ) -> List[float]:
        """
        Embed text using Gemini Embedding 2 Preview via Euri.

        Args:
            text: Text to embed (max 8192 tokens)
            dimensions: Optional dimension override (default 768)

        Returns:
            768-dimensional embedding vector

        Raises:
            APIError: If Euri API fails after retries
        """
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def embed_medical_content(
        self,
        content: str,
        content_type: str = "text",
        source_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Embed medical content with metadata for RAG.

        Used for:
        - Medical articles
        - Patient discharge summaries
        - Treatment guidelines
        - Clinical notes

        Args:
            content: Medical text content
            content_type: "text", "pdf", "image", "audio", "video"
            source_name: Original file name or source identifier

        Returns:
            Dictionary with embedding + metadata:
            {
                "embedding": [768 floats],
                "dimensions": 768,
                "source_type": "text",
                "source_name": "medical_article.pdf",
                "content_preview": "First 200 chars...",
                "tokens_used": 42
            }
        """
        try:
            # Chunk if text is very long (8192 token limit per request)
            if len(content) > 32000:  # ~8192 tokens * 4 chars/token
                logger.warning(f"Content too long ({len(content)} chars), truncating")
                content = content[:32000]

            embedding = self.embed_text(content)

            return {
                "embedding": embedding,
                "dimensions": self.embedding_dimensions,
                "source_type": content_type,
                "source_name": source_name or "unknown",
                "content_preview": content[:200],
                "tokens_used": len(content) // 4,  # Rough estimate
            }
        except APIError as e:
            logger.error(f"Medical embedding failed for {source_name}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_medical_response(
        self,
        patient_question: str,
        medical_context: str,
        patient_info: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> str:
        """
        Generate medical response using gpt-4o-mini via Euri.

        System prompt ensures:
        - Answers ONLY from retrieved context
        - No hallucinations
        - Appropriate medical disclaimers
        - Conservative recommendations

        Args:
            patient_question: Patient's query
            medical_context: Retrieved medical documents from Pinecone RAG
            patient_info: Optional patient metadata (age, allergies, medications)
            stream: If True, return generator for streaming (not implemented here)

        Returns:
            Medical response text

        Raises:
            APIError: If Euri LLM fails after retries
        """
        system_prompt = self._build_medical_system_prompt(patient_info)

        user_message = self._build_rag_message(
            patient_question,
            medical_context,
            patient_info,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.3,  # Low creativity for medical facts
                max_tokens=2048,
                stream=stream,
            )

            if stream:
                return response  # Generator object for streaming

            return response.choices[0].message.content

        except APIError as e:
            logger.error(f"Euri LLM generation failed: {e}")
            raise

    def _build_medical_system_prompt(
        self,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build system prompt for medical assistant."""
        base_prompt = """You are a medical AI assistant providing health information to patients.

CRITICAL RULES:
1. Answer ONLY from the retrieved medical context provided below
2. If the context is insufficient, SAY SO - do not hallucinate
3. Always include a disclaimer: "This is for informational purposes only, not medical advice"
4. Flag any critical symptoms that require immediate medical attention (chest pain, severe breathing difficulty, etc.)
5. Recommend consulting a doctor for diagnosis or treatment decisions
6. Be conservative and cautious in your recommendations
7. Never prescribe medications or provide dosing advice
8. Cite your sources (document title, section) when referencing specific information
"""

        if patient_info:
            base_prompt += f"""

PATIENT CONTEXT:
- Age: {patient_info.get('age', 'Unknown')}
- Allergies: {patient_info.get('allergies', 'None noted')}
- Current medications: {patient_info.get('medications', 'None noted')}
- Medical history: {patient_info.get('history', 'Not provided')}
"""

        return base_prompt

    def _build_rag_message(
        self,
        patient_question: str,
        medical_context: str,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build user message with RAG context."""
        message = f"""Retrieved Medical Information:
{'-' * 50}
{medical_context}
{'-' * 50}

Patient Question: {patient_question}

Answer based ONLY on the retrieved context above."""

        return message

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_orchestrator_response(
        self,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrator agent: analyzes intent and routes to specialist agents.

        Routes to:
        - Clinical Agent (medical knowledge)
        - RAG Agent (document retrieval)
        - Medication Agent (drug interactions)
        - Triage Agent (urgency assessment)

        Args:
            user_message: Patient message
            chat_history: Previous conversation

        Returns:
            {
                "routing_intent": "clinical|rag|medication|triage",
                "confidence": 0.95,
                "reason": "User asked about symptoms",
                "agent_to_call": "clinical_agent"
            }
        """
        routing_prompt = """You are the orchestrator agent for a medical AI assistant.
Your job is to analyze patient messages and route them to the correct specialist agent.

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
}
"""

        history_context = ""
        if chat_history:
            history_context = "\nChat history:\n"
            for msg in chat_history[-3:]:  # Last 3 messages
                history_context += f"- {msg['role']}: {msg['content'][:100]}\n"

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": routing_prompt},
                    {
                        "role": "user",
                        "content": f"Patient message: {user_message}{history_context}",
                    },
                ],
                temperature=0.3,
                max_tokens=256,
            )

            import json

            result = json.loads(response.choices[0].message.content)
            return result

        except (APIError, json.JSONDecodeError) as e:
            logger.error(f"Orchestrator routing failed: {e}")
            # Fallback: route to clinical agent
            return {
                "routing_intent": "clinical",
                "confidence": 0.5,
                "reason": "Fallback routing due to API error",
                "agent_to_call": "clinical_agent",
            }

    def health_check(self) -> bool:
        """Test Euri API connectivity."""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input="Health check",
                dimensions=self.embedding_dimensions,
            )
            return len(response.data[0].embedding) == self.embedding_dimensions
        except Exception as e:
            logger.error(f"Euri health check failed: {e}")
            return False


# Singleton instance for application
_euri_service: Optional[EuriService] = None


def get_euri_service() -> EuriService:
    """Get or create Euri service instance."""
    global _euri_service
    if _euri_service is None:
        _euri_service = EuriService()
    return _euri_service
