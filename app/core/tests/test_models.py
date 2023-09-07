"""
Tests for models
"""
from django.test import TestCase

from django.contrib.auth import get_user_model


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
