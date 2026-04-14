from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Book
from .services.rag import ask_question as rag_ask_question


class BookApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.primary = Book.objects.create(
            title="Mystery Manor",
            author="Author A",
            description="A detective investigates a murder in an old manor.",
            rating=4.6,
            url="https://example.com/mystery-manor",
            summary="A short mystery summary.",
            genre="Mystery",
        )
        Book.objects.create(
            title="City Clues",
            author="Author B",
            description="A mystery thriller with clues across the city.",
            rating=4.8,
            url="https://example.com/city-clues",
            summary="A second mystery summary.",
            genre="Mystery",
        )
        Book.objects.create(
            title="Space Drift",
            author="Author C",
            description="A sci-fi adventure in deep space.",
            rating=4.0,
            url="https://example.com/space-drift",
            summary="A sci-fi summary.",
            genre="Science Fiction",
        )

    def test_list_books(self):
        response = self.client.get("/books", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 3)
        self.assertIn("title", payload[0])
        self.assertIn("author", payload[0])
        self.assertIn("rating", payload[0])

    def test_recommendations_prefers_same_genre(self):
        response = self.client.get(f"/recommend/{self.primary.id}", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        recommendations = payload.get("recommendations", [])
        self.assertTrue(recommendations)
        self.assertEqual(recommendations[0]["genre"], "Mystery")

    @patch("books.views.ask_question")
    def test_ask_question_endpoint(self, mock_ask_question):
        mock_ask_question.return_value = {
            "question": "What is this book about?",
            "answer": "It is about solving a mystery. [S1]",
            "sources": [
                {
                    "citation": "S1",
                    "book_id": self.primary.id,
                    "title": self.primary.title,
                    "author": self.primary.author,
                    "url": self.primary.url,
                    "chunk_index": 0,
                    "source_text": self.primary.description,
                    "distance": 0.1,
                }
            ],
            "retrieval_mode": "vector",
        }

        response = self.client.post(
            "/ask-question",
            data={"question": "What is this book about?"},
            format="json",
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["retrieval_mode"], "vector")
        self.assertIn("[S1]", payload["answer"])

    @patch("books.views.upsert_book_embedding")
    @patch("books.views.classify_genre")
    @patch("books.views.generate_summary")
    @patch("books.views.scrape_books")
    def test_upload_books_from_scraper(
        self,
        mock_scrape_books,
        mock_generate_summary,
        mock_classify_genre,
        mock_upsert_book_embedding,
    ):
        mock_scrape_books.return_value = [
            {
                "title": "Book One",
                "rating": 4.3,
                "description": "An uplifting story about growth.",
                "url": "https://example.com/book-one",
            },
            {
                "title": "Book Two",
                "rating": 4.1,
                "description": "A practical guide to productivity habits.",
                "url": "https://example.com/book-two",
            },
        ]
        mock_generate_summary.side_effect = lambda description: f"Summary: {description[:20]}"
        mock_classify_genre.return_value = "Self Help"
        mock_upsert_book_embedding.return_value = {"status": "indexed"}

        response = self.client.post(
            "/upload-book",
            data={"max_books": 2, "headless": True},
            format="json",
            HTTP_HOST="localhost",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["created"], 2)
        self.assertEqual(payload["embeddings_indexed"], 2)
        self.assertEqual(Book.objects.filter(title="Book One").count(), 1)
        self.assertEqual(Book.objects.filter(title="Book Two").count(), 1)


class RagFallbackTests(TestCase):
    def setUp(self):
        Book.objects.create(
            title="Practical Habits",
            author="A. Writer",
            description="This book explains productivity habits and daily focus routines.",
            rating=4.4,
            url="https://example.com/practical-habits",
            summary="Productivity and mindset guide.",
            genre="Self Help",
        )

    @patch("books.services.rag.answer_with_context", return_value="Keyword fallback answer [S1]")
    @patch("books.services.rag.query_similar_book_content", side_effect=RuntimeError("vector failure"))
    def test_rag_keyword_fallback_when_vector_fails(self, _mock_query, _mock_answer):
        result = rag_ask_question("Which book helps with productivity habits?")

        self.assertEqual(result["retrieval_mode"], "keyword_fallback")
        self.assertTrue(result["sources"])
        self.assertIn("[S1]", result["answer"])
