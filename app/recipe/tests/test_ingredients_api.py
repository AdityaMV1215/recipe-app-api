"""
Tests for Ingredient APIs.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


def detail_url(ingredient_id):
    """Return the detail url for a ingredient with ingredient_id."""
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="user@example.com", password="test-pass-123"):
    """Create and return a user."""
    return get_user_model().objects.create_user(email, password)


class PublicIngredientsAPITests(TestCase):
    """Tests for ingredients api from unauthenticated user."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to retrieve ingredients."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsAPITests(TestCase):
    """Tests for ingredients api from authenticated user."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test for retrieving all ingredients for a user."""
        Ingredient.objects.create(user=self.user, name="Ingredient1")
        Ingredient.objects.create(user=self.user, name="Ingredient2")

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        """Test retrieved ingredients are limited to the authenticated user."""
        other_user = create_user(email="other-user@example.com",
                                 password="test-pass-123")
        Ingredient.objects.create(user=other_user,
                                  name="Other User Ingredient1")
        Ingredient.objects.create(user=other_user,
                                  name="Other User Ingredient2")

        Ingredient.objects.create(user=self.user, name="Ingredient1")
        Ingredient.objects.create(user=self.user, name="Ingredient2")

        res = self.client.get(INGREDIENTS_URL)

        user_ingredients = Ingredient.objects.filter(
            user=self.user
            ).order_by(
                "-name"
            )
        other_user_ingredients = Ingredient.objects.filter(
            user=other_user
            ).order_by(
                "-name"
            )

        user_serializer = IngredientSerializer(user_ingredients, many=True)
        other_user_serializer = IngredientSerializer(
            other_user_ingredients,
            many=True,
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, user_serializer.data)
        self.assertNotIn(res.data, other_user_serializer.data)

    def test_update_ingredient(self):
        """Test to update a ingredient."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Ingredient1",
        )

        payload = {"name": "Ingredient1-Updated"}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        ingredient.refresh_from_db()

        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test for deleting a ingredient."""
        ingredient = Ingredient.objects.create(
            user=self.user,
            name="Ingredient1",
        )

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(id=ingredient.id)

        self.assertFalse(ingredients.exists())
