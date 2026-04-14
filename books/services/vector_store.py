import os
import re
from hashlib import sha1
from math import sqrt
from pathlib import Path
from typing import Any

import chromadb
from django.conf import settings
from sentence_transformers import SentenceTransformer

_model_instance: SentenceTransformer | None = None
_collection_instance = None


def _embedding_model_name() -> str:
    return os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")


def _chroma_db_path() -> str:
    configured = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    path = Path(configured)
    if not path.is_absolute():
        path = Path(settings.BASE_DIR) / path
    return str(path)


def _collection_name() -> str:
    return os.getenv("CHROMA_COLLECTION_NAME", "books")


def _chunk_size_words() -> int:
    raw = os.getenv("CHUNK_SIZE_WORDS", "120")
    try:
        value = int(raw)
    except ValueError:
        value = 120
    return max(40, value)


def _chunk_overlap_words() -> int:
    raw = os.getenv("CHUNK_OVERLAP_WORDS", "30")
    try:
        value = int(raw)
    except ValueError:
        value = 30
    return max(0, min(value, _chunk_size_words() - 1))


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return []

    words = text.split(" ")
    chunk_size = chunk_size or _chunk_size_words()
    overlap = _chunk_overlap_words() if overlap is None else max(0, overlap)
    step = max(1, chunk_size - overlap)

    chunks = []
    for start in range(0, len(words), step):
        piece = words[start : start + chunk_size]
        if not piece:
            continue
        chunks.append(" ".join(piece))
        if start + chunk_size >= len(words):
            break
    return chunks


def _get_model() -> SentenceTransformer:
    global _model_instance
    if _model_instance is None:
        _model_instance = SentenceTransformer(_embedding_model_name())
    return _model_instance


def _get_collection():
    global _collection_instance
    if _collection_instance is None:
        client = chromadb.PersistentClient(path=_chroma_db_path())
        _collection_instance = client.get_or_create_collection(name=_collection_name())
    return _collection_instance


def create_description_embedding(description: str) -> list[float]:
    return create_text_embedding(description)


def _fallback_embedding(text: str, dim: int = 384) -> list[float]:
    """
    Deterministic local embedding fallback used when transformer models are unavailable.
    Keeps RAG APIs functional in offline/dev environments.
    """
    vector = [0.0] * dim
    for token in re.findall(r"[A-Za-z0-9']+", text.lower()):
        bucket = int(sha1(token.encode("utf-8")).hexdigest(), 16) % dim
        vector[bucket] += 1.0

    norm = sqrt(sum(value * value for value in vector))
    if norm > 0:
        vector = [value / norm for value in vector]
    return vector


def create_text_embedding(text: str) -> list[float]:
    text = (text or "").strip()
    if not text:
        raise ValueError("Input text is empty. Cannot generate embedding.")

    try:
        model = _get_model()
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()
    except Exception:
        return _fallback_embedding(text)


def upsert_book_embedding(book) -> dict[str, Any]:
    description = (book.description or "").strip()
    if not description:
        return {
            "book_id": book.id,
            "status": "skipped",
            "reason": "Empty description",
        }

    description_hash = sha1(description.encode("utf-8")).hexdigest()
    chunks = chunk_text(description)
    if not chunks:
        return {
            "book_id": book.id,
            "status": "skipped",
            "reason": "Unable to chunk description",
        }

    collection = _get_collection()
    try:
        existing = collection.get(
            where={"book_id": int(book.id)},
            include=["metadatas"],
            limit=1,
        )
    except Exception:
        existing = {"metadatas": []}

    existing_metadatas = existing.get("metadatas") or []
    existing_hash = None
    if existing_metadatas and isinstance(existing_metadatas, list):
        first = existing_metadatas[0] or {}
        if isinstance(first, dict):
            existing_hash = first.get("description_hash")

    if existing_hash == description_hash:
        return {
            "book_id": book.id,
            "status": "skipped",
            "reason": "Description unchanged",
            "collection": _collection_name(),
            "chunks_indexed": 0,
        }

    embeddings = [create_text_embedding(chunk) for chunk in chunks]
    ids = [f"{book.id}_chunk_{idx}" for idx in range(len(chunks))]
    metadatas = [
        {
            "book_id": int(book.id),
            "title": book.title,
            "author": book.author,
            "url": book.url,
            "chunk_index": idx,
            "chunk_count": len(chunks),
            "description_hash": description_hash,
        }
        for idx in range(len(chunks))
    ]

    # Replace older vectors for this book so embeddings stay in sync after updates.
    collection.delete(where={"book_id": int(book.id)})
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    return {
        "book_id": book.id,
        "status": "indexed",
        "collection": _collection_name(),
        "chunks_indexed": len(chunks),
    }


def query_similar_book_content(
    question_text: str,
    n_results: int = 3,
    book_ids: list[int] | None = None,
) -> list[dict[str, Any]]:
    question_embedding = create_text_embedding(question_text)
    collection = _get_collection()

    query_kwargs: dict[str, Any] = {
        "query_embeddings": [question_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }

    if book_ids:
        query_kwargs["where"] = {"book_id": {"$in": [int(book_id) for book_id in book_ids]}}

    try:
        result = collection.query(**query_kwargs)
    except Exception:
        return []

    ids = result.get("ids", [[]])[0]
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    matches = []
    for idx, item_id in enumerate(ids):
        metadata = metadatas[idx] if idx < len(metadatas) and metadatas[idx] else {}
        matches.append(
            {
                "id": item_id,
                "source_text": documents[idx] if idx < len(documents) else "",
                "metadata": metadata,
                "distance": distances[idx] if idx < len(distances) else None,
            }
        )
    return matches
