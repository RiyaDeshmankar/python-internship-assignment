import { useEffect, useState } from "react";
import { askQuestion, fetchBooks } from "../api/client";

export default function QuestionAnswerPage() {
  const [books, setBooks] = useState([]);
  const [bookId, setBookId] = useState("");
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loadingBooks, setLoadingBooks] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function loadBooks() {
      try {
        setLoadingBooks(true);
        const data = await fetchBooks();
        if (mounted) {
          setBooks(data);
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || "Unable to load books.");
        }
      } finally {
        if (mounted) {
          setLoadingBooks(false);
        }
      }
    }
    loadBooks();
    return () => {
      mounted = false;
    };
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    try {
      setSubmitting(true);
      setError("");
      const response = await askQuestion(question.trim(), bookId || undefined);
      setResult(response);
    } catch (err) {
      setError(err.message || "Unable to fetch answer.");
      setResult(null);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-ink/10 bg-panel p-5 shadow-card">
        <h1 className="font-serif text-3xl text-ink">Question Answering</h1>
        <p className="mt-1 text-sm text-ink/70">
          Ask questions about all books or scope to one specific book.
        </p>

        <form className="mt-5 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.16em] text-ink/60">
              Select Book (Optional)
            </label>
            <select
              value={bookId}
              onChange={(event) => setBookId(event.target.value)}
              className="w-full rounded-xl border border-ink/20 bg-white px-3 py-2 text-sm outline-none ring-accent/30 focus:ring"
              disabled={loadingBooks}
            >
              <option value="">All books</option>
              {books.map((book) => (
                <option key={book.id} value={book.id}>
                  {book.title}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-[0.16em] text-ink/60">
              Your Question
            </label>
            <textarea
              rows={4}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Example: Which book is best for a beginner interested in mystery themes?"
              className="w-full rounded-xl border border-ink/20 bg-white px-3 py-2 text-sm outline-none ring-accent/30 focus:ring"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="rounded-full bg-ink px-6 py-2 text-sm font-medium text-white transition hover:bg-accent disabled:cursor-not-allowed disabled:bg-ink/50"
          >
            {submitting ? "Processing..." : "Ask Question"}
          </button>
        </form>
      </div>

      {error ? (
        <p className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</p>
      ) : null}

      {result ? (
        <div className="space-y-4 rounded-3xl border border-ink/10 bg-panel p-5">
          <article>
            <h2 className="font-serif text-2xl text-ink">Answer</h2>
            <p className="mt-2 text-xs font-medium uppercase tracking-[0.14em] text-ink/60">
              Retrieval Mode: {result.retrieval_mode || "vector"}
            </p>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink/85">
              {result.answer || "No answer generated."}
            </p>
          </article>

          <article>
            <h3 className="font-serif text-xl text-ink">Source Text</h3>
            {!result.sources || result.sources.length === 0 ? (
              <p className="mt-2 text-sm text-ink/70">No sources returned.</p>
            ) : (
              <ul className="mt-2 space-y-3">
                {result.sources.map((source, index) => (
                  <li key={`${source.book_id}-${index}`} className="rounded-xl border border-ink/10 bg-white/80 p-3">
                    <p className="text-sm font-semibold text-ink">
                      [{source.citation || `S${index + 1}`}] {source.title || "Unknown Title"}{" "}
                      {source.author ? `by ${source.author}` : ""}
                    </p>
                    <p className="mt-1 text-xs text-ink/60">{source.url || "No URL"}</p>
                    {source.chunk_index !== undefined && source.chunk_index !== null ? (
                      <p className="mt-1 text-xs text-ink/60">Chunk: {source.chunk_index}</p>
                    ) : null}
                    <p className="mt-2 text-sm leading-relaxed text-ink/80">
                      {source.source_text || "No source snippet available."}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </div>
      ) : null}
    </section>
  );
}
