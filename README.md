# AI-Powered Book Insight Platform

Full-stack document intelligence app for books using Django REST Framework + React/Tailwind, with scraping, AI-generated insights, and RAG-based Q&A with citations.

## Features

- Automated book ingestion using Selenium (`books.toscrape.com`)
- Metadata storage in Django models (supports MySQL or SQLite fallback)
- AI insight generation:
  - Summary generation
  - Genre classification
  - Related-book recommendations
- RAG pipeline:
  - Chunking with overlap
  - Embedding generation
  - ChromaDB similarity search
  - Contextual answers with source citations
  - Keyword fallback retrieval when vector retrieval is unavailable
- React + Tailwind frontend pages:
  - Dashboard / Book listing
  - Book detail page
  - Q&A interface

## Tech Stack

- Backend: Django, Django REST Framework, Selenium
- Database: MySQL (assignment target), SQLite (dev fallback), ChromaDB (vector store)
- Embeddings: Sentence Transformers (`all-MiniLM-L6-v2`) + deterministic local fallback
- AI: OpenAI-compatible API (OpenAI / LM Studio) with local fallback logic
- Frontend: React (Vite) + Tailwind CSS

## Project Structure

```text
backend/                 Django project settings/urls
books/                   Django app (models, views, services, scrapers)
frontend/                React + Tailwind app
samples/                 Sample payloads/questions for testing
chroma_db/               Persistent vector database
```

## Setup Instructions

### 1) Backend setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

Create `.env` from `.env.example`:

```bash
copy .env.example .env
```

For quick local run, keep:

```env
DB_ENGINE=sqlite
```

For assignment-compliant metadata storage, configure MySQL and set:

```env
DB_ENGINE=mysql
MYSQL_DATABASE=book_ai
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

Run backend:

```bash
python manage.py migrate
python manage.py runserver
```

### 2) Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Optional API target for separate dev servers:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Build production frontend:

```bash
npm run build
```

## API Documentation

Base URL: `http://127.0.0.1:8000`

### Core endpoints

- `GET /books` - list all books
- `GET /books/{id}` - get book details
- `GET /recommend/{id}` - related book recommendations
- `POST /upload-book` - scrape and save books
- `POST /ask-question` - ask RAG question (optionally scoped by `book_id`)
- `GET /api/books/` - namespaced list endpoint
- `POST /api/books/upload/` - manual book upload

### Example: scrape/upload books

```bash
curl -X POST http://127.0.0.1:8000/upload-book \
  -H "Content-Type: application/json" \
  -d "{\"max_books\": 20, \"headless\": true}"
```

### Example: ask a question

```bash
curl -X POST http://127.0.0.1:8000/ask-question \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Which book is best for building better habits?\"}"
```

Expected response shape:

```json
{
  "question": "Which book is best for building better habits?",
  "answer": "... [S1] ...",
  "sources": [
    {
      "citation": "S1",
      "book_id": 1,
      "title": "Atomic Habits",
      "author": "James Clear",
      "url": "https://example.com/atomic-habits",
      "chunk_index": 0,
      "source_text": "...",
      "distance": 0.12
    }
  ],
  "retrieval_mode": "vector"
}
```

## Sample Questions and Answers

1. Question: `Which book helps improve daily habits?`  
   Sample answer: Recommends a self-help title with citations such as `[S1]`.

2. Question: `Suggest fantasy books with adventure.`  
   Sample answer: Returns fantasy books and related recommendation links.

3. Question: `Which book discusses survival on Mars?`  
   Sample answer: Returns a science-fiction answer grounded in retrieved source chunks.

Sample input data is provided in:

- `samples/books_sample.json`
- `samples/sample_questions.json`

## Screenshots

Add 3-4 UI screenshots under `docs/screenshots/` and keep this section updated:

- `docs/screenshots/dashboard.png`
- `docs/screenshots/book-detail.png`
- `docs/screenshots/qa-page.png`
- `docs/screenshots/qa-answer.png`

## Running Tests

```bash
python manage.py test
```

## Notes

- `DB_ENGINE=mysql` is supported for assignment requirements.
- `DB_ENGINE=sqlite` is provided for fast local onboarding.
- RAG endpoint now degrades gracefully if external embedding model download is unavailable.
