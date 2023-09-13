"""
Views for the Recipe APIs.
"""
from rest_framework import (
    viewsets,
    mixins,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (
    Recipe,
    Tag,
    Ingredient,
)

from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""
    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        return super().get_queryset() \
            .filter(user=self.request.user).order_by("-id")

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        return super().perform_create(serializer)


class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base View for recipe attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset() \
            .filter(user=self.request.user).order_by("-name")


class TagViewSet(BaseRecipeAttrViewSet):
    """View for manage tags APIs."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    """View for manage ingredients APIs."""
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
