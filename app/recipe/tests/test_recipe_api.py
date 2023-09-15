"""
Tests for Recipe APIs.
"""
from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe.serializers import (
        RecipeSerializer,
        RecipeDetailSerializer,
    )


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return a recipe detail URL using recipe_id."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return image URL"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


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

    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags."""
        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal("2.50"),
            "tags": [{"name": "Thai"}, {"name": "Dinner"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        exists = True
        for tag in payload["tags"]:
            exists = exists and recipe.tags.filter(
                name=tag["name"],
                user=self.user
            ).exists()
        self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating recipe with 1 existing and 1 new tag."""
        tag_indian = Tag.objects.create(user=self.user, name="Indian")

        payload = {
            "title": "Butter Chicken",
            "time_minutes": 120,
            "price": Decimal("9.99"),
            "tags": [{"name": "Indian"}, {"name": "Dinner"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        exists = True
        for tag in payload["tags"]:
            exists = exists and recipe.tags.filter(
                name=tag["name"],
                user=self.user
            ).exists()
        self.assertTrue(exists)

    def test_create_tag_in_recipe_update(self):
        """Test if tag is created when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "Lunch"}]}

        url = detail_url(recipe_id=recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_tag = Tag.objects.get(user=self.user,
                                  name=payload["tags"][0]["name"])

        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_existing_tag(self):
        """Test assigning an existing tag when updating a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "Breakfast"}]}

        url = detail_url(recipe_id=recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_breakfast, recipe.tags.all())

    def test_update_recipe_replace_tag(self):
        """Test replacing an existing tag on a recipe."""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        payload = {"tags": [{"name": "Lunch"}]}

        url = detail_url(recipe_id=recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        exists = True
        for tag in payload["tags"]:
            exists = exists and recipe.tags.filter(
                user=self.user,
                **tag
            ).exists()
        self.assertTrue(exists)
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients."""
        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal("2.50"),
            "ingredients": [{"name": "Prawn"}, {"name": "Coconut Milk"}],
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        exists = True
        for ingredient in payload["ingredients"]:
            exists = exists and recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user
            ).exists()
        self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """Test creating recipe with 1 existing and 1 new ingredient."""
        ingredient_indian = Ingredient.objects.create(
            user=self.user,
            name="Curry",
        )

        payload = {
            "title": "Butter Chicken",
            "time_minutes": 120,
            "price": Decimal("9.99"),
            "ingredients": [{"name": "Curry"}, {"name": "Chilly"}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)

        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient_indian, recipe.ingredients.all())
        exists = True
        for ingredient in payload["ingredients"]:
            exists = exists and recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user
            ).exists()
        self.assertTrue(exists)

    def test_create_ingredient_in_recipe_update(self):
        """Test if ingredient is created when updating a recipe."""
        recipe = create_recipe(user=self.user)

        payload = {"ingredients": [{"name": "Curry"}]}

        url = detail_url(recipe_id=recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.get(
            user=self.user,
            name=payload["ingredients"][0]["name"],
        )

        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_existing_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe."""
        ingredient_breakfast = Ingredient.objects.create(
            user=self.user,
            name="Egg"
        )
        recipe = create_recipe(user=self.user)

        payload = {"ingredients": [{"name": "Egg"}]}

        url = detail_url(recipe_id=recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient_breakfast, recipe.ingredients.all())

    def test_update_recipe_replace_ingredient(self):
        """Test replacing an existing ingredient on a recipe."""
        ingredient_breakfast = Ingredient.objects.create(
            user=self.user,
            name="Egg"
        )
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient_breakfast)

        payload = {"ingredients": [{"name": "Bread"}]}

        url = detail_url(recipe_id=recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        exists = True
        for ingredient in payload["ingredients"]:
            exists = exists and recipe.ingredients.filter(
                user=self.user,
                **ingredient
            ).exists()
        self.assertTrue(exists)
        self.assertNotIn(ingredient_breakfast, recipe.ingredients.all())


class ImageUploadTests(TestCase):
    """Tests for image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="test-pass-123",
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self) -> None:
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_invalid_image(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.recipe.id)
        payload = {"image": "notanimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
