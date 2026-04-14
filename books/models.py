from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField()
    rating = models.FloatField(null=True)
    url = models.URLField()
    summary = models.TextField(null=True)
    genre = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.title
