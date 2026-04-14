import logging

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book
from .scrapers import scrape_books
from .serializers import BookQuestionSerializer, BookSerializer
from .services.ai_service import classify_genre, generate_summary
from .services.rag import ask_question
from .services.vector_store import upsert_book_embedding

logger = logging.getLogger(__name__)


class BookAutoInsightCreateMixin:
    def perform_create(self, serializer):
        validated_data = serializer.validated_data
        description = validated_data.get("description", "")
        summary = validated_data.get("summary") or generate_summary(description)
        genre = validated_data.get("genre") or classify_genre(description)
        book = serializer.save(summary=summary, genre=genre)

        try:
            upsert_book_embedding(book)
        except Exception:
            logger.exception(
                "Failed to generate/store embedding for book_id=%s",
                getattr(book, "id", None),
            )


class BookListCreateView(BookAutoInsightCreateMixin, generics.ListCreateAPIView):
    queryset = Book.objects.all().order_by("title")
    serializer_class = BookSerializer


class BookUploadView(BookAutoInsightCreateMixin, generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BookRecommendationView(APIView):
    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)

        related = Book.objects.exclude(pk=book.pk)
        if book.genre:
            related = related.filter(genre__iexact=book.genre)

        if not related.exists() and book.author:
            related = Book.objects.exclude(pk=book.pk).filter(author__iexact=book.author)

        if not related.exists():
            related = Book.objects.exclude(pk=book.pk)

        recommendations = related.order_by("-rating", "title")[:5]
        payload = {
            "book": BookSerializer(book).data,
            "recommendations": BookSerializer(recommendations, many=True).data,
        }
        return Response(payload, status=status.HTTP_200_OK)


class BookQueryView(APIView):
    def post(self, request):
        serializer = BookQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        book_id = serializer.validated_data.get("book_id")
        book_ids = None

        if book_id is not None:
            if not Book.objects.filter(pk=book_id).exists():
                return Response(
                    {"detail": "No books found for the given scope."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            book_ids = [book_id]

        try:
            result = ask_question(question=question, book_ids=book_ids)
        except Exception:
            logger.exception("RAG query failed for question=%r", question)
            result = {
                "question": question,
                "answer": "Unable to process this question right now. Please try again.",
                "sources": [],
                "retrieval_mode": "unavailable",
            }
        return Response(result, status=status.HTTP_200_OK)


class UploadBooksFromScraperView(APIView):
    @staticmethod
    def _parse_headless(raw_value):
        if isinstance(raw_value, bool):
            return raw_value
        if raw_value is None:
            return True
        return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _parse_max_books(raw_value):
        if raw_value in (None, ""):
            return None
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            return "invalid"
        return value if value > 0 else "invalid"

    def post(self, request):
        max_books = self._parse_max_books(request.data.get("max_books"))
        headless = self._parse_headless(request.data.get("headless", True))

        if max_books == "invalid":
            return Response(
                {"detail": "max_books must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            scraped_books = scrape_books(max_books=max_books, headless=headless)
        except Exception as exc:
            return Response(
                {"detail": "Scraping failed.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        created_count = 0
        updated_count = 0
        embeddings_indexed = 0
        embedding_errors = 0
        saved_books = []

        for item in scraped_books:
            title = item.get("title", "").strip()
            description = (item.get("description") or "").strip()
            rating = item.get("rating")
            url = item.get("url")

            if not title or not url:
                continue

            defaults = {
                "title": title,
                "author": "Unknown",
                "description": description,
                "rating": rating,
                "summary": generate_summary(description),
                "genre": classify_genre(description),
            }

            book, created = Book.objects.update_or_create(url=url, defaults=defaults)
            if created:
                created_count += 1
            else:
                updated_count += 1

            try:
                embedding_result = upsert_book_embedding(book)
                if embedding_result.get("status") == "indexed":
                    embeddings_indexed += 1
            except Exception:
                embedding_errors += 1
                logger.exception(
                    "Failed to generate/store embedding for book_id=%s",
                    getattr(book, "id", None),
                )

            saved_books.append(
                {
                    "id": book.id,
                    "title": book.title,
                    "url": book.url,
                    "rating": book.rating,
                }
            )

        return Response(
            {
                "message": "Scraping completed and books saved.",
                "total_scraped": len(scraped_books),
                "created": created_count,
                "updated": updated_count,
                "embeddings_indexed": embeddings_indexed,
                "embedding_errors": embedding_errors,
                "books": saved_books,
            },
            status=status.HTTP_200_OK,
        )
