"""
Tests for book APIs.
"""

from unittest.mock import patch
from datetime import datetime
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Book
from core import models
from book.serializers import BookSerializer

import tempfile
import os
from PIL import Image

BOOK_URL = reverse("book:book-list")


def image_upload_url(book_id):
    """Create and return an image upload URL."""
    return reverse("book:book-upload-image", args=[book_id])


def create_book(user, **params):
    """Create and return a sample book"""
    defaults = {
        "title": "Sample book title",
        "author": "sample author name",
        "release_date": "2030-09-12",
        "genre": "sample genre",
        "description": "sample desc",
    }
    defaults.update(params)

    book = Book.objects.create(user=user, **defaults)
    return book


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicBookAPITests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(BOOK_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateBookAPITests(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="test123")
        self.user = get_user_model().objects.create_user(
            "testone@example.com",
            "testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_retrieving_book(self):
        """Test retrieving a list of books"""
        create_book(user=self.user)
        create_book(user=self.user)

        res = self.client.get(BOOK_URL)

        book = Book.objects.all().order_by("-id")
        serializer = BookSerializer(book, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_book_list_limited_to_user(self):
        """Test list of books is limited to authenticated user."""
        other_user = create_user(email="other@example.com", password="test123")

        create_book(user=other_user)
        create_book(user=self.user)

        res = self.client.get(BOOK_URL)

        books = Book.objects.filter(user=self.user)
        serializer = BookSerializer(books, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_book(self):
        """Test creating a book"""
        payload = {
            "title": "Sample book title",
            "author": "sample author name",
            "release_date": "2000-08-14",
            "genre": "sample genre",
            "description": "sample desc",
        }
        res = self.client.post(BOOK_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(id=res.data["id"])
        for k, v in payload.items():
            if k == "release_date":
                expected_date = datetime.strptime(v, "%Y-%m-%d").date()
                self.assertEqual(getattr(book, k), expected_date)
            else:
                self.assertEqual(getattr(book, k), v)
        self.assertEqual(book.user, self.user)

    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test generating image path."""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.book_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/book/{uuid}.jpg")


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@example.com",
            "password123",
        )
        self.client.force_authenticate(self.user)
        self.book = create_book(user=self.user)

    def tearDown(self):
        self.book.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a book"""
        url = image_upload_url(self.book.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"image": image_file}
            res = self.client.post(url, payload, format="multipart")

        self.book.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.book.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.book.id)
        payload = {"image": "notanimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
