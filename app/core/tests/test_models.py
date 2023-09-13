"""
Tests for models
"""
from decimal import Decimal

from core import models

from django.test import TestCase

from django.contrib.auth import get_user_model


def create_user(email="user@example.com", password="test-pass-123"):
    """Create and return a user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Tests for models"""

    def test_create_user_with_email_successful(self):
        "Test for creating user with email"
        email = "test@example.com"
        password = "testpass123"
        new_user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(new_user.email, email)
        self.assertTrue(new_user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test to check if new user's email is normalized"""

        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"]
        ]

        for email, expected in sample_emails:
            new_user = get_user_model().objects.create_user(email, "sample123")
            self.assertEqual(new_user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test to check if new user without email fails"""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

    def test_create_superuser(self):
        """Test to check if superuser is created"""

        new_user = get_user_model().objects.create_superuser(
            email="test@example.com",
            password="testpass123"
        )

        self.assertTrue(new_user.is_superuser)
        self.assertTrue(new_user.is_staff)

    def test_create_recipe(self):
        """Test for creating a recipe is successful."""
        user = get_user_model().objects.create_user(
            email="test@example.com",
            password="test-pass-123",
            name="Test User",
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample Recipe Title",
            description="Sample Recipe Description",
            price=Decimal("5.50"),
            time_minutes=5,
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test for creating a tag."""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)
