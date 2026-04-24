"""Clinical Agent - medical knowledge & symptom analysis via Euri + FAISS RAG.

This agent:
1. Embeds patient question using Euri
2. Retrieves relevant medical context from FAISS
3. Generates evidence-based response using Euri LLM
4. Cites sources from medical knowledge base

Follows clean architecture: no direct API calls, delegates to services.
"""

import logging
from typing import Optional, Dict, Any
from app.services.euri_service import get_euri_service
from app.services.faiss_service import get_faiss_service

logger = logging.getLogger(__name__)


class ClinicalAgent:
    """Medical knowledge assistant with RAG from FAISS."""

    def __init__(self):
        """Initialize agent with Euri and FAISS services."""
        self.euri = get_euri_service()
        self.faiss = get_faiss_service()
        self.agent_name = "clinical"

    def answer_medical_question(
        self,
        patient_question: str,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Answer medical question with evidence-based response from RAG.

        Flow:
        1. Embed question with Euri
        2. Search FAISS for relevant medical documents
        3. Generate response using Euri LLM + context
        4. Return response + sources + confidence

        Args:
            patient_question: Patient's medical question
            patient_info: Optional patient metadata (age, allergies, meds)

        Returns:
            {
                "response": "Medical answer...",
                "sources": [
                    {"file": "guidelines.pdf", "excerpt": "...", "relevance": 0.92},
                ],
                "confidence_score": 0.95,
                "agent_used": "clinical",
                "tokens_used": 1024
            }
        """
        try:
            logger.info(f"Clinical agent processing: {patient_question[:100]}...")

            # Step 1: Embed the question
            question_embedding = self.euri.embed_text(patient_question)
            logger.debug("Question embedded")

            # Step 2: Retrieve relevant medical context from FAISS
            context_docs = self.faiss.search_medical_context(
                query_embedding=question_embedding,
                top_k=5,
                source_types=["text", "pdf"],  # Medical articles/guidelines
            )
            logger.info(f"Retrieved {len(context_docs)} documents")

            # Format context for LLM
            formatted_context = self.faiss.retrieve_medical_context(
                query_embedding=question_embedding,
                patient_id=patient_info.get("patient_id") if patient_info else None,
                top_k=5,
            )

            # Step 3: Generate medical response
            response_text = self.euri.generate_medical_response(
                patient_question=patient_question,
                medical_context=formatted_context,
                patient_info=patient_info,
                stream=False,
            )
            logger.debug("Response generated")

            # Step 4: Prepare sources
            sources = [
                {
                    "file": doc["source_file"],
                    "type": doc["source_type"],
                    "relevance": f"{doc['score']:.1%}",
                    "excerpt": doc["content_preview"][:150],
                }
                for doc in context_docs[:3]  # Top 3 sources
            ]

            # Calculate confidence based on context quality
            avg_relevance = (
                sum(doc["score"] for doc in context_docs) / len(context_docs)
                if context_docs
                else 0.5
            )

            return {
                "response": response_text,
                "sources": sources,
                "confidence_score": min(0.99, avg_relevance),  # Cap at 0.99
                "agent_used": self.agent_name,
                "tokens_used": int(len(response_text.split()) * 1.3),
                "context_documents_used": len(context_docs),
            }

        except Exception as e:
            logger.error(f"Clinical agent failed: {e}")
            return {
                "response": f"Medical Assistant Error: {str(e)}. Please try again.",
                "sources": [],
                "confidence_score": 0.0,
                "agent_used": self.agent_name,
                "error": str(e),
            }

    def analyze_symptoms(
        self,
        symptoms: str,
        duration: Optional[str] = None,
        patient_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze patient symptoms with differential diagnosis considerations.

        Args:
            symptoms: Description of symptoms
            duration: How long symptoms have persisted
            patient_info: Patient metadata

        Returns:
            {
                "summary": "Your symptoms may suggest...",
                "possible_conditions": [...],
                "next_steps": "You should see a doctor...",
                "emergency_warning_signs": ["Severe chest pain", ...],
                "confidence_score": 0.85
            }
        """
        try:
            # Build detailed symptom question
            question = f"Patient symptoms: {symptoms}"
            if duration:
                question += f" (duration: {duration})"

            logger.info(f"Analyzing symptoms: {symptoms[:100]}...")

            # Use medical RAG to get context
            question_embedding = self.euri.embed_text(question)
            context = self.faiss.retrieve_medical_context(
                query_embedding=question_embedding,
                patient_id=patient_info.get("patient_id") if patient_info else None,
            )

            # Enhanced prompt for symptom analysis
            analysis_prompt = f"""
Based on the medical literature below, analyze these patient symptoms.

SYMPTOMS: {symptoms}
DURATION: {duration or "Not specified"}

Provide:
1. Brief summary of what these symptoms may suggest
2. 2-3 possible conditions (differential diagnosis)
3. When to seek immediate medical attention (red flags)
4. Next recommended steps (self-care vs doctor visit)

ALWAYS include disclaimer: This is for informational purposes only, not medical advice.
"""

            response = self.euri.generate_medical_response(
                patient_question=analysis_prompt,
                medical_context=context,
                patient_info=patient_info,
                stream=False,
            )

            return {
                "analysis": response,
                "symptoms_analyzed": symptoms,
                "agent_used": self.agent_name,
                "confidence_score": 0.85,
            }

        except Exception as e:
            logger.error(f"Symptom analysis failed: {e}")
            return {
                "analysis": "Unable to analyze symptoms at this time.",
                "error": str(e),
                "agent_used": self.agent_name,
            }

    def ingest_medical_document(
        self,
        content: str,
        source_type: str,
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Add new medical document to FAISS knowledge base.

        This ingests guidelines, articles, clinical notes, etc.

        Args:
            content: Document text content
            source_type: "text", "pdf", "article"
            source_name: Filename or title
            metadata: Additional metadata (author, date, category)

        Returns:
            {
                "success": True,
                "document_id": 123,
                "document_name": "guidelines.pdf",
                "chunks_added": 1,
                "message": "Added to medical knowledge base"
            }
        """
        try:
            logger.info(f"Ingesting document: {source_name}")

            # Embed the document content
            embedded = self.euri.embed_medical_content(
                content=content,
                content_type=source_type,
                source_name=source_name,
            )

            # Add to FAISS knowledge base
            doc_id = self.faiss.add_medical_document(
                embedding=embedded["embedding"],
                source_type=source_type,
                source_file=source_name,
                content_preview=embedded["content_preview"],
                metadata=metadata,
            )

            logger.info(f"Document ingested with ID: {doc_id}")

            return {
                "success": True,
                "document_id": doc_id,
                "document_name": source_name,
                "chunks_added": 1,
                "tokens_processed": embedded["tokens_used"],
                "message": f"Added to medical knowledge base (ID: {doc_id})",
            }

        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            return {
                "success": False,
                "document_name": source_name,
                "error": str(e),
                "message": "Failed to ingest document",
            }

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about ingested medical documents."""
        try:
            stats = self.faiss.stats()
            docs = self.faiss.list_documents()

            return {
                "total_documents": stats["total_vectors"],
                "document_types": stats["source_types"],
                "knowledge_base_size_mb": stats["index_file_size_mb"],
                "recent_documents": [
                    {
                        "id": d["id"],
                        "name": d["source_file"],
                        "type": d["source_type"],
                        "added": d["timestamp"],
                    }
                    for d in docs[:10]
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


def get_clinical_agent() -> ClinicalAgent:
    """Get or create clinical agent instance."""
    return ClinicalAgent()
