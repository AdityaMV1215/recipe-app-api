"""
Tests for Tag APIs.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Tag,
    Recipe,
)

from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id):
    """Return the detail url for a tag with tag_id."""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="test-pass-123"):
    """Create and return a user."""
    return get_user_model().objects.create_user(email, password)


class PublicTagsAPITests(TestCase):
    """Tests for tags api from unauthenticated user."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to retrieve tags."""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Tests for tags api from authenticated user."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test for retrieving all tags for a user."""
        Tag.objects.create(user=self.user, name="Tag1")
        Tag.objects.create(user=self.user, name="Tag2")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test retrieved tags are limited to the authenticated user."""
        other_user = create_user(email="other-user@example.com",
                                 password="test-pass-123")
        Tag.objects.create(user=other_user, name="Other User Tag1")
        Tag.objects.create(user=other_user, name="Other User Tag2")

        Tag.objects.create(user=self.user, name="Tag1")
        Tag.objects.create(user=self.user, name="Tag2")

        res = self.client.get(TAGS_URL)

        user_tags = Tag.objects.filter(user=self.user).order_by("-name")
        other_user_tags = Tag.objects.filter(user=other_user).order_by("-name")

        user_serializer = TagSerializer(user_tags, many=True)
        other_user_serializer = TagSerializer(other_user_tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, user_serializer.data)
        self.assertNotIn(res.data, other_user_serializer.data)

    def test_update_tag(self):
        """Test to update a tag."""
        tag = Tag.objects.create(user=self.user, name="Tag1")

        payload = {"name": "Tag1-Updated"}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()

        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test for deleting a tag."""
        tag = Tag.objects.create(user=self.user, name="Tag1")

        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = Tag.objects.filter(id=tag.id)

        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipe(self):
        """Test for filtering tags that are assigned to recipes."""
        i1 = Tag.objects.create(
            user=self.user,
            name="Tag1",
        )
        i2 = Tag.objects.create(
            user=self.user,
            name="Tag2",
        )
        i3 = Tag.objects.create(
            user=self.user,
            name="Tag3"
        )

        r1 = Recipe.objects.create(
            user=self.user,
            title="Recipe 1",
            time_minutes=30,
            price=Decimal("5.99"),
            description="Test Recipe 1",
        )
        r1.tags.add(i1)
        r1.tags.add(i2)

        payload = {"assigned_only": 1}

        res = self.client.get(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        s1 = TagSerializer(i1)
        s2 = TagSerializer(i2)
        s3 = TagSerializer(i3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filtered_tags_unique(self):
        """Test if filtered tags are unique."""
        i1 = Tag.objects.create(
            user=self.user,
            name="Tag1",
        )
        Tag.objects.create(
            user=self.user,
            name="Tag2",
        )

        r1 = Recipe.objects.create(
            user=self.user,
            title="Recipe 1",
            time_minutes=30,
            price=Decimal("5.99"),
            description="Test Recipe 1",
        )
        r2 = Recipe.objects.create(
            user=self.user,
            title="Recipe 2",
            time_minutes=30,
            price=Decimal("5.99"),
            description="Test Recipe 2",
        )

        r1.tags.add(i1)
        r2.tags.add(i1)

        payload = {"assigned_only": 1}

        res = self.client.get(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
