"""FAISS vector database service - local medical document embeddings.

FAISS (Facebook AI Similarity Search) stores 768-dimensional vectors locally.
No cloud dependency, perfect for development & learning.

Index structure:
- faiss_index.bin: Actual vector index (binary)
- faiss_metadata.json: Document metadata (JSON)
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import faiss
import numpy as np

logger = logging.getLogger(__name__)


class FAISSService:
    """Manage medical document vectors locally with FAISS."""

    def __init__(self):
        """Initialize FAISS service with local index."""
        self.index_path = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
        self.embedding_dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))

        # Create data directory if needed
        os.makedirs(self.index_path, exist_ok=True)

        # Paths for index and metadata
        self.index_file = os.path.join(self.index_path, "faiss_index.bin")
        self.metadata_file = os.path.join(self.index_path, "faiss_metadata.json")

        # Load or create index
        self.index = self._load_or_create_index()
        self.metadata = self._load_metadata()

        # Counter for document IDs
        self.next_id = len(self.metadata)

    def _load_or_create_index(self) -> faiss.IndexFlatL2:
        """Load existing FAISS index or create new one."""
        try:
            if os.path.exists(self.index_file):
                logger.info(f"Loading FAISS index from {self.index_file}")
                return faiss.read_index(self.index_file)

            logger.info(f"Creating new FAISS index (dim={self.embedding_dimensions})")
            # L2 (Euclidean distance) is standard; can also use IP (inner product)
            return faiss.IndexFlatL2(self.embedding_dimensions)

        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            raise

    def _load_metadata(self) -> Dict[int, Dict[str, Any]]:
        """Load metadata for stored vectors."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, "r") as f:
                    # Convert string keys to ints
                    raw = json.load(f)
                    return {int(k): v for k, v in raw.items()}
            return {}
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            return {}

    def _save_metadata(self) -> bool:
        """Persist metadata to disk."""
        try:
            # Convert int keys to strings for JSON
            data = {str(k): v for k, v in self.metadata.items()}
            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            return False

    def _save_index(self) -> bool:
        """Persist FAISS index to disk."""
        try:
            faiss.write_index(self.index, self.index_file)
            logger.debug(f"Saved FAISS index ({self.index.ntotal} vectors)")
            return True
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False

    def add_medical_document(
        self,
        embedding: List[float],
        source_type: str,
        source_file: str,
        content_preview: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_index: int = 0,
    ) -> int:
        """
        Add medical document embedding to FAISS.

        Args:
            embedding: 768-dimensional vector from Euri
            source_type: "text", "pdf", "image", "audio", "video"
            source_file: Original filename
            content_preview: First 200 chars of content
            metadata: Additional metadata (patient_id, date, author, etc.)
            chunk_index: Position in document (for chunked documents)

        Returns:
            Document ID in index
        """
        try:
            # Prepare vector (FAISS expects numpy arrays)
            vector = np.array([embedding], dtype=np.float32)

            # Add to index
            self.index.add(vector)
            doc_id = self.next_id

            # Store metadata
            self.metadata[doc_id] = {
                "id": doc_id,
                "source_type": source_type,
                "source_file": source_file,
                "chunk_index": chunk_index,
                "content_preview": content_preview,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Merge with optional metadata
            if metadata:
                self.metadata[doc_id].update(metadata)

            self.next_id += 1

            # Persist to disk
            self._save_index()
            self._save_metadata()

            logger.info(
                f"Added document {doc_id}: {source_file} ({source_type})"
            )
            return doc_id

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise

    def add_batch(
        self,
        embeddings: List[List[float]],
        source_type: str,
        source_files: List[str],
        content_previews: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[int]:
        """
        Add batch of documents to FAISS.

        Args:
            embeddings: List of 768-dimensional vectors
            source_type: Type for all documents
            source_files: List of filenames
            content_previews: List of preview texts
            metadatas: Optional list of metadata dicts

        Returns:
            List of document IDs
        """
        try:
            doc_ids = []

            # Convert to numpy array
            vectors = np.array(embeddings, dtype=np.float32)

            # Add all at once
            self.index.add(vectors)

            # Store metadata for each
            for i, (source_file, preview) in enumerate(
                zip(source_files, content_previews)
            ):
                doc_id = self.next_id + i

                self.metadata[doc_id] = {
                    "id": doc_id,
                    "source_type": source_type,
                    "source_file": source_file,
                    "chunk_index": 0,
                    "content_preview": preview,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                if metadatas and i < len(metadatas):
                    self.metadata[doc_id].update(metadatas[i])

                doc_ids.append(doc_id)

            self.next_id += len(embeddings)

            # Persist
            self._save_index()
            self._save_metadata()

            logger.info(f"Batch added {len(doc_ids)} documents")
            return doc_ids

        except Exception as e:
            logger.error(f"Batch add failed: {e}")
            raise

    def search_medical_context(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        source_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant medical documents via semantic similarity.

        Uses L2 (Euclidean) distance - lower is more similar.

        Args:
            query_embedding: Patient question embedding (768 dims)
            top_k: Number of results
            source_types: Filter by source type (["text", "pdf"])

        Returns:
            List of matching documents with scores:
            [
                {
                    "id": 0,
                    "score": 0.45,  # L2 distance (lower = better)
                    "source_type": "pdf",
                    "source_file": "guidelines.pdf",
                    "content_preview": "Treatment involves...",
                    "metadata": {...}
                },
                ...
            ]
        """
        try:
            if self.index.ntotal == 0:
                logger.warning("FAISS index is empty")
                return []

            # Prepare query
            query = np.array([query_embedding], dtype=np.float32)

            # Search
            distances, indices = self.index.search(query, min(top_k * 2, self.index.ntotal))

            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx == -1:  # Invalid result
                    continue

                meta = self.metadata.get(int(idx))
                if not meta:
                    continue

                # Filter by source type if requested
                if source_types and meta["source_type"] not in source_types:
                    continue

                # Convert L2 distance to similarity score (0-1, higher=better)
                # Normalize by dimension: smaller distance = higher similarity
                similarity = 1.0 / (1.0 + float(distance))

                results.append(
                    {
                        "id": int(idx),
                        "score": similarity,
                        "distance": float(distance),
                        "source_type": meta["source_type"],
                        "source_file": meta["source_file"],
                        "content_preview": meta["content_preview"],
                        "metadata": meta,
                    }
                )

            # Sort by score and limit to top_k
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def retrieve_medical_context(
        self,
        query_embedding: List[float],
        patient_id: Optional[str] = None,
        top_k: int = 5,
    ) -> str:
        """
        Retrieve and format medical context for RAG prompt.

        Args:
            query_embedding: Query vector
            patient_id: Optional filter
            top_k: Number of documents

        Returns:
            Formatted context string for LLM
        """
        try:
            matches = self.search_medical_context(
                query_embedding=query_embedding,
                top_k=top_k,
            )

            # Filter by patient if provided
            if patient_id:
                matches = [
                    m
                    for m in matches
                    if m["metadata"].get("patient_id") == patient_id
                ]

            if not matches:
                return "No relevant medical context found in knowledge base."

            context = "RETRIEVED MEDICAL INFORMATION:\n"
            context += "=" * 60 + "\n\n"

            for idx, match in enumerate(matches, 1):
                context += f"Document {idx}: {match['source_file']}\n"
                context += f"Source Type: {match['source_type']}\n"
                context += f"Relevance: {match['score']:.1%}\n"
                context += f"Content: {match['content_preview']}\n"
                context += "-" * 40 + "\n\n"

            return context

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return "Error retrieving medical context."

    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID."""
        return self.metadata.get(doc_id)

    def list_documents(
        self,
        source_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all documents, optionally filtered by source type."""
        docs = list(self.metadata.values())

        if source_type:
            docs = [d for d in docs if d["source_type"] == source_type]

        return sorted(docs, key=lambda d: d["timestamp"], reverse=True)

    def delete_document(self, doc_id: int) -> bool:
        """
        Delete document (note: FAISS doesn't support deletion directly).
        We mark as deleted in metadata.
        """
        try:
            if doc_id in self.metadata:
                # Mark as deleted instead of actual deletion
                self.metadata[doc_id]["deleted"] = True
                self._save_metadata()
                logger.info(f"Marked document {doc_id} as deleted")
                return True
            return False
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def clear_all(self) -> bool:
        """Clear all vectors and metadata (caution!)."""
        try:
            self.index = faiss.IndexFlatL2(self.embedding_dimensions)
            self.metadata = {}
            self.next_id = 0
            self._save_index()
            self._save_metadata()
            logger.warning("Cleared all FAISS data")
            return True
        except Exception as e:
            logger.error(f"Clear failed: {e}")
            return False

    def stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.embedding_dimensions,
            "index_type": "FlatL2 (Euclidean)",
            "index_file_size_mb": (
                os.path.getsize(self.index_file) / 1024 / 1024
                if os.path.exists(self.index_file)
                else 0
            ),
            "metadata_count": len(self.metadata),
            "source_types": list(set(m["source_type"] for m in self.metadata.values())),
        }

    def health_check(self) -> bool:
        """Test FAISS connectivity."""
        try:
            # Try a dummy search
            test_vector = np.array([[0.0] * self.embedding_dimensions], dtype=np.float32)
            self.index.search(test_vector, 1)
            return True
        except Exception as e:
            logger.error(f"FAISS health check failed: {e}")
            return False


# Singleton instance
_faiss_service: Optional[FAISSService] = None


def get_faiss_service() -> FAISSService:
    """Get or create FAISS service instance."""
    global _faiss_service
    if _faiss_service is None:
        _faiss_service = FAISSService()
    return _faiss_service
