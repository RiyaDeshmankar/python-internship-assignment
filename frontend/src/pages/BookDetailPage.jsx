import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchBookById, fetchRecommendations } from "../api/client";

export default function BookDetailPage() {
  const { id } = useParams();
  const [book, setBook] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadData() {
      try {
        setLoading(true);
        const [bookData, recommendData] = await Promise.all([
          fetchBookById(id),
          fetchRecommendations(id)
        ]);

        if (mounted) {
          setBook(bookData);
          setRecommendations(recommendData);
          setError("");
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || "Unable to load book details.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => {
      mounted = false;
    };
  }, [id]);

  if (loading) {
    return <p className="rounded-2xl bg-panel/80 p-4 text-sm text-ink/70">Loading book details...</p>;
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
        <p>{error}</p>
        <Link className="mt-3 inline-block text-sm font-medium underline" to="/">
          Back to dashboard
        </Link>
      </div>
    );
  }

  if (!book) {
    return <p className="rounded-2xl bg-panel/80 p-4 text-sm text-ink/70">Book not found.</p>;
  }

  return (
    <section className="space-y-5">
      <div className="rounded-3xl border border-ink/10 bg-panel p-6 shadow-card">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accentWarm">
          {book.genre || "General"}
        </p>
        <h1 className="mt-2 font-serif text-4xl leading-tight text-ink">{book.title}</h1>
        <p className="mt-2 text-sm text-ink/70">Author: {book.author || "Unknown"}</p>
        <p className="mt-1 text-sm text-ink/70">Rating: {book.rating ?? "N/A"}</p>
        <a
          href={book.url}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-block rounded-full bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-ink"
        >
          Open Original Book URL
        </a>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-3xl border border-ink/10 bg-panel p-5">
          <h2 className="font-serif text-2xl text-ink">Summary</h2>
          <p className="mt-3 text-sm leading-relaxed text-ink/80">
            {book.summary || "No summary available yet."}
          </p>
        </article>

        <article className="rounded-3xl border border-ink/10 bg-panel p-5">
          <h2 className="font-serif text-2xl text-ink">Description</h2>
          <p className="mt-3 text-sm leading-relaxed text-ink/80">
            {book.description || "No description available."}
          </p>
        </article>
      </div>

      <article className="rounded-3xl border border-ink/10 bg-panel p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-serif text-2xl text-ink">Related Recommendations</h2>
          <Link to="/qa" className="text-sm font-medium text-accent hover:text-ink">
            Ask a Question
          </Link>
        </div>

        {recommendations.length === 0 ? (
          <p className="mt-3 text-sm text-ink/70">No recommendations found yet.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {recommendations.map((item) => (
              <li
                key={item.id}
                className="rounded-xl border border-ink/10 bg-white/70 px-3 py-2 text-sm text-ink/80"
              >
                <Link to={`/book/${item.id}`} className="font-medium text-ink hover:text-accent">
                  {item.title}
                </Link>{" "}
                by {item.author || "Unknown"} (Rating: {item.rating ?? "N/A"})
              </li>
            ))}
          </ul>
        )}
      </article>
    </section>
  );
}
