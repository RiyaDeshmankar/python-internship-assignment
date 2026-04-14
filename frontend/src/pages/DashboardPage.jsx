import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { fetchBooks, uploadBooks } from "../api/client";

function BookCard({ book }) {
  return (
    <article className="rounded-3xl border border-ink/10 bg-panel p-5 shadow-card">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accentWarm">
        {book.genre || "General"}
      </p>
      <h3 className="mt-2 font-serif text-2xl leading-tight text-ink">{book.title}</h3>
      <p className="mt-1 text-sm text-ink/70">by {book.author || "Unknown"}</p>

      <p className="mt-3 text-sm leading-relaxed text-ink/80">
        {book.summary || "No summary available yet."}
      </p>
      <p className="mt-2 text-sm leading-relaxed text-ink/70">
        {book.description || "No description available."}
      </p>

      {book.url ? (
        <a
          href={book.url}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-xs font-medium text-accent underline-offset-2 hover:underline"
        >
          {book.url}
        </a>
      ) : null}

      <div className="mt-4 flex items-center justify-between gap-3">
        <span className="rounded-full bg-accent/10 px-3 py-1 text-xs font-medium text-accent">
          Rating: {book.rating ?? "N/A"}
        </span>
        <Link
          to={`/book/${book.id}`}
          className="rounded-full bg-ink px-4 py-2 text-sm font-medium text-white transition hover:bg-accent"
        >
          View Details
        </Link>
      </div>
    </article>
  );
}

export default function DashboardPage() {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [maxBooks, setMaxBooks] = useState(20);
  const [uploading, setUploading] = useState(false);
  const [uploadSummary, setUploadSummary] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadBooks() {
      try {
        setLoading(true);
        const data = await fetchBooks();
        if (mounted) {
          setBooks(data);
          setError("");
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || "Unable to load books.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadBooks();
    return () => {
      mounted = false;
    };
  }, []);

  const filteredBooks = useMemo(() => {
    if (!searchTerm.trim()) {
      return books;
    }
    const q = searchTerm.trim().toLowerCase();
    return books.filter((book) =>
      [book.title, book.author, book.genre, book.description]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }, [books, searchTerm]);

  async function handleUploadBooks() {
    try {
      setUploading(true);
      setError("");
      setUploadSummary("");
      const response = await uploadBooks(maxBooks);
      const refreshed = await fetchBooks();
      setBooks(refreshed);
      setUploadSummary(
        [
          `Scraped ${response?.total_scraped ?? 0}`,
          `created ${response?.created ?? 0}`,
          `updated ${response?.updated ?? 0}`,
          `indexed ${response?.embeddings_indexed ?? 0}`,
        ].join(" | ")
      );
    } catch (err) {
      setError(err.message || "Unable to upload books.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section>
      <div className="mb-5 rounded-3xl border border-ink/10 bg-panel/90 p-4 sm:p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="font-serif text-3xl text-ink">Dashboard</h1>
            <p className="mt-1 text-sm text-ink/70">
              Browse uploaded books and open details or Q&A.
            </p>
          </div>

          <div className="w-full sm:w-80">
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-ink/60">
              Search Books
            </label>
            <input
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Title, author, genre..."
              className="w-full rounded-xl border border-ink/20 bg-white px-3 py-2 text-sm outline-none ring-accent/30 focus:ring"
            />
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-end">
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-ink/60">
              Max Books to Scrape
            </label>
            <input
              type="number"
              min="1"
              value={maxBooks}
              onChange={(event) => setMaxBooks(Math.max(1, Number(event.target.value) || 1))}
              className="w-44 rounded-xl border border-ink/20 bg-white px-3 py-2 text-sm outline-none ring-accent/30 focus:ring"
            />
          </div>
          <button
            type="button"
            onClick={handleUploadBooks}
            disabled={uploading}
            className="rounded-full bg-accent px-5 py-2 text-sm font-medium text-white transition hover:bg-ink disabled:cursor-not-allowed disabled:opacity-70"
          >
            {uploading ? "Uploading..." : "Scrape & Upload Books"}
          </button>
        </div>
        {uploadSummary ? (
          <p className="mt-3 rounded-xl bg-emerald-50 px-3 py-2 text-xs text-emerald-700">{uploadSummary}</p>
        ) : null}
      </div>

      {loading ? (
        <p className="rounded-2xl bg-panel/80 p-4 text-sm text-ink/70">Loading books...</p>
      ) : null}

      {error ? (
        <p className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</p>
      ) : null}

      {!loading && !error && filteredBooks.length === 0 ? (
        <p className="rounded-2xl bg-panel/80 p-4 text-sm text-ink/70">
          No books found. Upload books from your backend endpoint and refresh.
        </p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filteredBooks.map((book) => (
          <BookCard key={book.id} book={book} />
        ))}
      </div>
    </section>
  );
}
