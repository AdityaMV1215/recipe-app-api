"""
Serializers for Recipe APIs.
"""
from rest_framework import serializers

from core.models import Recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for the Recipe Model."""

    class Meta:
        model = Recipe
        fields = ["id", "title", "price", "time_minutes", "link"]
        read_only_fields = ["id"]


class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for Recipe Detail."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description"]
