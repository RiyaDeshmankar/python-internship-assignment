from django.urls import path

from .views import (
    BookDetailView,
    BookListCreateView,
    BookQueryView,
    BookRecommendationView,
    BookUploadView,
    UploadBooksFromScraperView,
)

urlpatterns = [
    path("books/", BookListCreateView.as_view(), name="book-list-create"),
    path("books/upload/", BookUploadView.as_view(), name="book-upload"),
    path("upload-book/", UploadBooksFromScraperView.as_view(), name="upload-book-api"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book-detail"),
    path("recommend/<int:pk>/", BookRecommendationView.as_view(), name="recommend-book-api"),
    path(
        "books/<int:pk>/recommendations/",
        BookRecommendationView.as_view(),
        name="book-recommendations",
    ),
    path("books/query/", BookQueryView.as_view(), name="book-query"),
    path("ask-question/", BookQueryView.as_view(), name="ask-question-api"),
    path("upload-books/", UploadBooksFromScraperView.as_view(), name="upload-books"),
]
