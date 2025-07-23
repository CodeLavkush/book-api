"""
Database models
"""
import uuid
import os
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


def book_image_file_path(instance, filename):
    """Generate file path for new book image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'book', filename)


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError("User must have an email address")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create, save and return a new super user"""
        user = self.create_user(email, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"


class Book(models.Model):
    """Book objects."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    release_date = models.DateField()
    genre = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(null=True, upload_to=book_image_file_path)

    def __str__(self):
        return self.title
