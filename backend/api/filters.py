from django_filters import rest_framework as filters

from menu.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",
        to_field_name="slug",
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_is_in_cart")

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if value and user and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_cart(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if value and user and user.is_authenticated:
            return queryset.filter(shopping_cart_items__user=user)
        return queryset
