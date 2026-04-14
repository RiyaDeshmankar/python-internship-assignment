"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path, re_path

from books.views import (
    BookDetailView,
    BookListCreateView,
    BookQueryView,
    BookRecommendationView,
    UploadBooksFromScraperView,
)
from .views import api_home, frontend_home

urlpatterns = [
    path("", frontend_home, name="frontend-home"),
    path("api-info/", api_home, name="api-home"),
    path("admin/", admin.site.urls),
    path("books", BookListCreateView.as_view(), name="books"),
    path("books/<int:pk>", BookDetailView.as_view(), name="book-detail"),
    path("recommend/<int:pk>", BookRecommendationView.as_view(), name="recommend-book"),
    path("upload-book", UploadBooksFromScraperView.as_view(), name="upload-book"),
    path("ask-question", BookQueryView.as_view(), name="ask-question"),
    path("upload-books/", UploadBooksFromScraperView.as_view(), name="upload-books-root"),
    path("api/", include("books.urls")),
    re_path(r"^(qa|book/.*)$", frontend_home, name="frontend-routes"),
]
