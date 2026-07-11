"""
RAG Engine - Retrieval Augmented Generation for NCCR
"""
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from database.models import DocumentChunk, Patient
from typing import List, Dict
import numpy as np

# Multilingual model — your documents mix Russian/Kazakh/English medical
# text; all-MiniLM-L6-v2 is English-centric and gives noisy similarity on
# non-English content. Same 384-dim output, no schema changes needed.
embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')


def chunk_text(text: str, chunk_size: int = 150, overlap: int = 30) -> List[str]:
    """
    Flat word-count chunking with overlap. This is the version that
    measured 0.456 Context Precision — your best confirmed result so far.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    step = max(chunk_size - overlap, 1)

    for i in range(0, len(words), step):
        chunk_words = words[i:i + chunk_size]
        if not chunk_words:
            break
        chunks.append(' '.join(chunk_words))
        if i + chunk_size >= len(words):
            break

    return chunks


def store_document_chunks(
    db: Session,
    patient_id: int,
    text: str,
    source_type: str
):
    """Chunk document, create embeddings, save to database"""

    chunks = chunk_text(text)

    if not chunks:
        print(f"No chunks generated for patient {patient_id} (empty text)")
        return

    embeddings = embedding_model.encode(chunks)

    for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        doc_chunk = DocumentChunk(
            patient_id=patient_id,
            source_type=source_type,
            chunk_text=chunk,
            chunk_index=index,
            embedding=embedding.tolist()
        )
        db.add(doc_chunk)

    db.commit()
    print(f"Stored {len(chunks)} chunks for patient {patient_id}")


def search_chunks(
    db: Session,
    query: str,
    patient_id: int = None,
    top_k: int = 3
) -> List[Dict]:
    """Find most relevant chunks for a question"""

    query_embedding = embedding_model.encode([query])[0]

    if patient_id:
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.patient_id == patient_id
        ).all()
    else:
        chunks = db.query(DocumentChunk).all()

    if not chunks:
        return []

    chunk_matrix = np.array([c.embedding for c in chunks])
    query_vec = np.array(query_embedding)

    similarities = _cosine_similarity_batch(query_vec, chunk_matrix)

    results = []
    for chunk, similarity in zip(chunks, similarities):
        results.append({
            'chunk_text': chunk.chunk_text,
            'similarity': float(similarity),
            'patient_id': chunk.patient_id,
            'source_type': chunk.source_type
        })

    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]


def _cosine_similarity_batch(query_vec: np.ndarray, chunk_matrix: np.ndarray) -> np.ndarray:
    query_norm = np.linalg.norm(query_vec)
    chunk_norms = np.linalg.norm(chunk_matrix, axis=1)
    denom = query_norm * chunk_norms
    denom[denom == 0] = 1e-10
    return (chunk_matrix @ query_vec) / denom


def calculate_similarity(vec1: List[float], vec2: List[float]) -> float:
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    denom = np.linalg.norm(v1) * np.linalg.norm(v2)
    if denom == 0:
        return 0.0
    return float(np.dot(v1, v2) / denom)