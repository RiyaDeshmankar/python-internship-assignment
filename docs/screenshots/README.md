# Screenshots

Capture and place UI screenshots in this folder with these names:

- `dashboard.png`
- `book-detail.png`
- `qa-page.png`
- `qa-answer.png`

Suggested capture flow:

1. Run backend: `python manage.py runserver`
2. Run frontend: `cd frontend && npm run dev` (or use Django-served build)
3. Capture desktop screenshots for `/`, `/book/{id}`, `/qa`
4. Capture one screenshot of Q&A after submitting a question
