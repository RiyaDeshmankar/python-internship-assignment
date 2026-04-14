const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "")
  : "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (error) {
    payload = null;
  }

  if (!response.ok) {
    const message = payload?.detail || payload?.error || "Request failed";
    throw new Error(message);
  }

  return payload;
}

export async function fetchBooks() {
  const data = await request("/books");
  return Array.isArray(data) ? data : data?.results || [];
}

export function fetchBookById(id) {
  return request(`/books/${id}`);
}

export async function fetchRecommendations(id) {
  const data = await request(`/recommend/${id}`);
  return data?.recommendations || [];
}

export function askQuestion(question, bookId) {
  const body = { question };
  if (bookId) {
    body.book_id = Number(bookId);
  }

  return request("/ask-question", {
    method: "POST",
    body: JSON.stringify(body)
  });
}

export function uploadBooks(maxBooks = 20) {
  const safeMaxBooks = Math.max(1, Number(maxBooks) || 1);
  return request("/upload-book", {
    method: "POST",
    body: JSON.stringify({ max_books: safeMaxBooks, headless: true })
  });
}
