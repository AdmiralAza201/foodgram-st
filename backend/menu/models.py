from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models

from core.constants import (
    COOKING_TIME_MAX,
    COOKING_TIME_MIN,
    HEX_COLOR_PATTERN,
    INGREDIENT_AMOUNT_MIN,
    INGREDIENT_AMOUNT_MAX,
    INGREDIENT_NAME_MAX_LENGTH,
    INGREDIENT_UNIT_MAX_LENGTH,
    RECIPE_NAME_MAX_LENGTH,
    SHORT_LINK_CODE_MAX_LENGTH,
    TAG_COLOR_DEFAULT,
    TAG_COLOR_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
)

COOKING_TIME_MIN_MESSAGE = " ".join(
    [
        "Время приготовления не может быть меньше",
        "{value} минуты.",
    ]
)
COOKING_TIME_MAX_MESSAGE = " ".join(
    [
        "Время приготовления не может превышать",
        "{value} минут.",
    ]
)
INGREDIENT_MIN_MESSAGE = " ".join(
    [
        "Количество не может быть меньше",
        "{value}.",
    ]
)
INGREDIENT_MAX_MESSAGE = " ".join(
    [
        "Количество не может превышать",
        "{value}.",
    ]
)

CTIME_MIN_ERROR = COOKING_TIME_MIN_MESSAGE.format(value=COOKING_TIME_MIN)
CTIME_MAX_ERROR = COOKING_TIME_MAX_MESSAGE.format(value=COOKING_TIME_MAX)
ING_MIN_ERROR = INGREDIENT_MIN_MESSAGE.format(value=INGREDIENT_AMOUNT_MIN)
ING_MAX_ERROR = INGREDIENT_MAX_MESSAGE.format(value=INGREDIENT_AMOUNT_MAX)


class Tag(models.Model):
    name = models.CharField(
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        verbose_name="Название",
    )
    color = models.CharField(
        max_length=TAG_COLOR_MAX_LENGTH,
        unique=True,
        verbose_name="Цвет",
        default=TAG_COLOR_DEFAULT,
        validators=[
            RegexValidator(
                regex=HEX_COLOR_PATTERN,
                message="Цвет указывается в HEX-формате (#RRGGBB).",
            )
        ],
    )
    slug = models.SlugField(
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        verbose_name="Слаг",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        verbose_name="Название",
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_UNIT_MAX_LENGTH,
        verbose_name="Единица измерения",
    )

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_ingredient_name_unit",
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LENGTH,
        verbose_name="Название",
    )
    image = models.ImageField(
        upload_to="recipes/",
        blank=True,
        null=True,
        verbose_name="Изображение",
    )
    text = models.TextField(verbose_name="Описание")
    cooking_time = models.PositiveIntegerField(
        validators=[
            MinValueValidator(
                COOKING_TIME_MIN,
                message=CTIME_MIN_ERROR,
            ),
            MaxValueValidator(
                COOKING_TIME_MAX,
                message=CTIME_MAX_ERROR,
            ),
        ],
        verbose_name="Время приготовления (мин)",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="Теги",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        related_name="recipes",
        verbose_name="Ингредиенты",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент",
    )
    amount = models.PositiveIntegerField(
        validators=[
            MinValueValidator(
                INGREDIENT_AMOUNT_MIN,
                message=ING_MIN_ERROR,
            ),
            MaxValueValidator(
                INGREDIENT_AMOUNT_MAX,
                message=ING_MAX_ERROR,
            ),
        ],
        verbose_name="Количество",
    )

    class Meta:
        default_related_name = "recipe_ingredients"
        ordering = ("recipe", "ingredient")
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_recipe_ingredient",
            )
        ]

    def __str__(self):
        return f"{self.ingredient} для {self.recipe}"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        default_related_name = "favorites"
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_favorite_user_recipe",
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.recipe}"


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
    )

    class Meta:
        default_related_name = "shopping_cart_items"
        verbose_name = "Элемент списка покупок"
        verbose_name_plural = "Список покупок"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_cart_user_recipe",
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.recipe}"


class ShortLinkRecipe(models.Model):
    recipe = models.OneToOneField(
        Recipe,
        on_delete=models.CASCADE,
        related_name="shortlink",
        verbose_name="Рецепт",
    )
    code = models.SlugField(
        max_length=SHORT_LINK_CODE_MAX_LENGTH,
        unique=True,
        verbose_name="Код",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создан",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Короткая ссылка"
        verbose_name_plural = "Короткие ссылки"

    def __str__(self):
        return f"Ссылка {self.code} для {self.recipe}"
