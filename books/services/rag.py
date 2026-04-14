import re

from django.db.models import Q

from ..models import Book
from .ai_service import answer_with_context
from .vector_store import query_similar_book_content


def _keyword_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9']+", (text or "").lower())
    return [token for token in tokens if len(token) >= 3]


def _source_text_for_book(book: Book) -> str:
    return (book.description or "").strip() or (book.summary or "").strip()


def _keyword_fallback_sources(question: str, book_ids: list[int] | None = None) -> list[dict]:
    queryset = Book.objects.all()
    if book_ids:
        queryset = queryset.filter(id__in=book_ids)

    tokens = _keyword_tokens(question)
    if tokens:
        search_query = Q()
        for token in tokens:
            search_query |= (
                Q(title__icontains=token)
                | Q(author__icontains=token)
                | Q(description__icontains=token)
                | Q(summary__icontains=token)
                | Q(genre__icontains=token)
            )
        queryset = queryset.filter(search_query).distinct()

    books = list(queryset.order_by("-rating", "title")[:5])
    sources = []
    for idx, book in enumerate(books, start=1):
        source_text = _source_text_for_book(book)
        if not source_text:
            continue
        sources.append(
            {
                "citation": f"S{idx}",
                "book_id": book.id,
                "title": book.title,
                "author": book.author,
                "url": book.url,
                "chunk_index": None,
                "source_text": source_text,
                "distance": None,
            }
        )
    return sources


def ask_question(question: str, book_ids: list[int] | None = None) -> dict:
    question = (question or "").strip()
    if not question:
        return {
            "question": question,
            "answer": "Question is empty. Please ask a valid question.",
            "sources": [],
        }

    try:
        matches = query_similar_book_content(
            question_text=question,
            n_results=5,
            book_ids=book_ids,
        )
    except Exception:
        matches = []

    if not matches:
        fallback_sources = _keyword_fallback_sources(question=question, book_ids=book_ids)
        if fallback_sources:
            answer = answer_with_context(question=question, context_chunks=fallback_sources)
            return {
                "question": question,
                "answer": answer,
                "sources": fallback_sources,
                "retrieval_mode": "keyword_fallback",
            }
        return {
            "question": question,
            "answer": "No relevant book context found. Upload and index books first.",
            "sources": [],
            "retrieval_mode": "vector",
        }

    sources = []
    for idx, match in enumerate(matches, start=1):
        metadata = match.get("metadata", {})
        source_text = (match.get("source_text") or "").strip()
        sources.append(
            {
                "citation": f"S{idx}",
                "book_id": metadata.get("book_id"),
                "title": metadata.get("title"),
                "author": metadata.get("author"),
                "url": metadata.get("url"),
                "chunk_index": metadata.get("chunk_index"),
                "source_text": source_text,
                "distance": match.get("distance"),
            }
        )

    answer = answer_with_context(question=question, context_chunks=sources)
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieval_mode": "vector",
    }
