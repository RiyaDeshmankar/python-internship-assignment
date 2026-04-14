import os
import re
from textwrap import shorten

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

GENRE_OPTIONS = [
    "Fantasy",
    "Science Fiction",
    "Mystery",
    "Romance",
    "Self Help",
    "General",
]

GENRE_KEYWORDS = {
    "Fantasy": ["magic", "dragon", "kingdom", "sword", "myth"],
    "Science Fiction": ["space", "robot", "future", "alien", "planet"],
    "Mystery": ["murder", "detective", "crime", "investigation", "clue"],
    "Romance": ["love", "relationship", "heart", "romantic", "couple"],
    "Self Help": ["habits", "mindset", "productivity", "success", "motivation"],
}


def _provider() -> str:
    return os.getenv("AI_PROVIDER", "local").strip().lower()


def _model_name() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def _openai_client():
    if OpenAI is None:
        return None

    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key and not base_url:
        return None

    if not api_key and base_url:
        # Many local OpenAI-compatible servers do not require a real key.
        api_key = "local-model-key"

    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _local_summary(description: str) -> str:
    cleaned = re.sub(r"\s+", " ", description or "").strip()
    if not cleaned:
        return "No description available."

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    candidate = " ".join(sentences[:2]) if len(sentences) > 1 else sentences[0]
    return shorten(candidate, width=300, placeholder="...")


def _local_genre(description: str) -> str:
    text = (description or "").lower()
    if not text:
        return "General"

    scores = {
        genre: sum(text.count(keyword) for keyword in keywords)
        for genre, keywords in GENRE_KEYWORDS.items()
    }
    best_genre = max(scores, key=scores.get)
    return best_genre if scores[best_genre] > 0 else "General"


def _openai_summary(description: str) -> str | None:
    client = _openai_client()
    if client is None:
        return None

    prompt = (
        "Summarize the following book description in 2-3 sentences.\n\n"
        f"Description:\n{description}"
    )
    try:
        response = client.responses.create(
            model=_model_name(),
            input=prompt,
            temperature=0.2,
            max_output_tokens=140,
        )
        text = (response.output_text or "").strip()
        return text or None
    except Exception:
        return None


def _openai_genre(description: str) -> str | None:
    client = _openai_client()
    if client is None:
        return None

    prompt = (
        "Classify this book description into exactly one genre from this list:\n"
        f"{', '.join(GENRE_OPTIONS)}\n\n"
        "Return only the genre label.\n\n"
        f"Description:\n{description}"
    )
    try:
        response = client.responses.create(
            model=_model_name(),
            input=prompt,
            temperature=0.0,
            max_output_tokens=20,
        )
        text = (response.output_text or "").strip()
        normalized = text.lower()
        for genre in GENRE_OPTIONS:
            if normalized == genre.lower():
                return genre
        for genre in GENRE_OPTIONS:
            if genre.lower() in normalized:
                return genre
        return None
    except Exception:
        return None


def generate_summary(description: str) -> str:
    description = (description or "").strip()
    if _provider() == "openai":
        summary = _openai_summary(description)
        if summary:
            return summary
    return _local_summary(description)


def classify_genre(description: str) -> str:
    description = (description or "").strip()
    if _provider() == "openai":
        genre = _openai_genre(description)
        if genre:
            return genre
    return _local_genre(description)


def _openai_answer_with_context(question: str, context_text: str) -> str | None:
    client = _openai_client()
    if client is None:
        return None

    prompt = (
        "You are answering a user question using only the provided book context.\n"
        "If context is insufficient, say so briefly.\n"
        "Include source references in the format [S1], [S2], etc.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question:\n{question}"
    )

    try:
        response = client.responses.create(
            model=_model_name(),
            input=prompt,
            temperature=0.1,
            max_output_tokens=260,
        )
        text = (response.output_text or "").strip()
        return text or None
    except Exception:
        return None


def _local_answer_with_context(question: str, context_chunks: list[dict]) -> str:
    if not context_chunks:
        return "I could not find relevant context to answer this question."

    lead = context_chunks[0]
    title = lead.get("title", "Unknown Title")
    snippet = lead.get("source_text", "").strip()
    snippet = shorten(re.sub(r"\s+", " ", snippet), width=320, placeholder="...")

    if not snippet:
        return "I found related sources, but they do not contain enough text to answer."

    return (
        f"From {title}, the most relevant information is: {snippet} [S1]. "
        f"This is the best available answer to: {question}"
    )


def answer_with_context(question: str, context_chunks: list[dict]) -> str:
    context_lines = []
    for idx, item in enumerate(context_chunks, start=1):
        title = item.get("title") or "Unknown Title"
        text = (item.get("source_text") or "").strip()
        text = re.sub(r"\s+", " ", text)
        text = shorten(text, width=900, placeholder="...")
        context_lines.append(f"[S{idx}] {title}: {text}")

    context_text = "\n".join(context_lines)
    llm_answer = _openai_answer_with_context(question=question, context_text=context_text)
    if llm_answer:
        if "[S" not in llm_answer and context_chunks:
            refs = ", ".join(f"[S{idx}]" for idx in range(1, len(context_chunks) + 1))
            return f"{llm_answer}\n\nSources: {refs}"
        return llm_answer

    return _local_answer_with_context(question=question, context_chunks=context_chunks)
