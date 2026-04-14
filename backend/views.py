from pathlib import Path

from django.http import JsonResponse
from django.shortcuts import render


def frontend_home(request):
    frontend_index = Path(__file__).resolve().parent.parent / "frontend" / "dist" / "index.html"
    if frontend_index.exists():
        return render(request, "index.html")
    return JsonResponse(
        {
            "message": "Frontend build not found.",
            "next_steps": [
                "cd frontend",
                "npm install",
                "npm run build",
            ],
        },
        status=503,
    )


def api_home(request):
    return JsonResponse(
        {
            "message": "Book Insight Backend is running.",
            "endpoints": {
                "list_books": "/books",
                "book_detail": "/books/{id}",
                "recommendations": "/recommend/{id}",
                "upload_book": "/upload-book",
                "ask_question": "/ask-question",
                "api_namespace": "/api/",
            },
        }
    )
