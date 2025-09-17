from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShortLinkRecipe,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorites_count')
    search_fields = ('name', 'author__username', 'author__email')
    inlines = [RecipeIngredientInline]

    def favorites_count(self, obj):
        return obj.favorited_by.count()

    favorites_count.short_description = 'В избранном (шт.)'


admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(ShortLinkRecipe)
