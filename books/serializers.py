from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"


class BookQuestionSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000)
    book_id = serializers.IntegerField(required=False)
