"""
Serializers for recipe APIs
"""

from rest_framework import serializers

from core.models import Book


class BookSerializer(serializers.ModelSerializer):
    """Serializer for books."""

    class Meta:
        model = Book
        fields = ["id", "title", "author", "release_date", "genre", "description", "image"]
        read_only_fields = ["id"]


class BookImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to books."""

    class Meta:
        model = Book
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {
            'image': {
                'required': 'True',
            }
        }