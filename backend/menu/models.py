from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=7, default="#FFFFFF")
    slug = models.SlugField(max_length=64, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=32)

    class Meta:
        unique_together = ('name', 'measurement_unit')
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    name = models.CharField(max_length=128)
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()
    tags = models.ManyToManyField(Tag, related_name='recipes')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    class Meta:
        unique_together = ('recipe', 'ingredient')


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )

    class Meta:
        unique_together = ('user', 'recipe')


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_carts',
    )

    class Meta:
        unique_together = ('user', 'recipe')


class ShortLinkRecipe(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shortlink',
    )
    code = models.SlugField(max_length=16, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
