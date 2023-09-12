"""
Tests for Recipe APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
        RecipeSerializer,
        RecipeDetailSerializer,
    )


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL using recipe_id."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    """Create a sample recipe."""
    defaults = {
        "title": "Sample Recipe Title",
        "description": "Sample Recipe Description",
        "price": Decimal("5.50"),
        "time_minutes": 22,
        "link": "http://www.example.com/recipe.pdf",
    }
    defaults.update(**params)

    recipe = Recipe.objects.create(user=user, **defaults)

    return recipe


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated Recipe API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_authentication_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authentication_required_for_recipe_detail(self):
        """Test auth is required for recipe detail."""
        unauthenticated_user = get_user_model().objects.create_user(
            email="unauth-user@example.com",
            password="test-pass-123",
        )
        recipe = create_recipe(user=unauthenticated_user)
        recipe_url = detail_url(recipe_id=recipe.id)

        res = self.client.get(recipe_url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated Recipe API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="test-pass-123"
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test for retrieving recipes list for an authenticated user."""
        create_recipe(user=self.user)
        create_recipe(self.user, title="Sample Recipe 2 Title",
                      description="Sample Recipe 2 Description",
                      link="http://www.example.com/recipe2.pdf")
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test for the retireved recipes are
        limited to the authenticated user."""
        other_user = get_user_model().objects.create_user(
            email="other-user@example.com",
            password="test-pass-123"
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        user_recipes = Recipe.objects.filter(user=self.user)
        user_serializer = RecipeSerializer(user_recipes, many=True)

        other_user_recipes = Recipe.objects.filter(user=other_user)
        other_user_serializer = RecipeSerializer(other_user_recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, user_serializer.data)
        self.assertNotIn(res.data, other_user_serializer.data)

    def test_retrieve_recipe_detail(self):
        """Test for retrieving recipe detail for authenticated user."""
        recipe = create_recipe(user=self.user)

        recipe_url = detail_url(recipe_id=recipe.id)

        res = self.client.get(recipe_url)
        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a new recipe for authenticated user."""
        payload = {
            "title": "Sample Recipe Title",
            "price": Decimal("5.99"),
            "time_minutes": 30
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        created_recipe = Recipe.objects.get(id=res.data["id"])

        for k, v in payload.items():
            self.assertEqual(getattr(created_recipe, k), v)
        self.assertEqual(created_recipe.user, self.user)
