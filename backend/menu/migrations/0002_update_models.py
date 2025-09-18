from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("menu", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="tag",
            options={
                "ordering": ("name",),
                "verbose_name": "Тег",
                "verbose_name_plural": "Теги",
            },
        ),
        migrations.AlterField(
            model_name="tag",
            name="color",
            field=models.CharField(
                default="#FFFFFF",
                max_length=7,
                unique=True,
                validators=[
                    RegexValidator(
                        message="Цвет указывается в HEX-формате (#RRGGBB).",
                        regex="^#[0-9A-Fa-f]{6}$",
                    )
                ],
                verbose_name="Цвет",
            ),
        ),
        migrations.AlterField(
            model_name="tag",
            name="name",
            field=models.CharField(
                max_length=200, unique=True, verbose_name="Название"
            ),
        ),
        migrations.AlterField(
            model_name="tag",
            name="slug",
            field=models.SlugField(max_length=200, unique=True, verbose_name="Слаг"),
        ),
        migrations.AlterModelOptions(
            name="ingredient",
            options={
                "ordering": ("name",),
                "verbose_name": "Ингредиент",
                "verbose_name_plural": "Ингредиенты",
            },
        ),
        migrations.AlterField(
            model_name="ingredient",
            name="measurement_unit",
            field=models.CharField(max_length=64, verbose_name="Единица измерения"),
        ),
        migrations.AlterUniqueTogether(
            name="ingredient",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="ingredient",
            constraint=models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="unique_ingredient_name_unit",
            ),
        ),
        migrations.AlterModelOptions(
            name="recipe",
            options={
                "ordering": ("-created_at",),
                "verbose_name": "Рецепт",
                "verbose_name_plural": "Рецепты",
            },
        ),
        migrations.AlterField(
            model_name="recipe",
            name="cooking_time",
            field=models.PositiveIntegerField(
                validators=[
                    MinValueValidator(
                        1, message="Время приготовления не может быть меньше 1 минуты."
                    ),
                    MaxValueValidator(
                        1440,
                        message="Время приготовления не может превышать 1440 минут.",
                    ),
                ],
                verbose_name="Время приготовления (мин)",
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="image",
            field=models.ImageField(
                blank=True, null=True, upload_to="recipes/", verbose_name="Изображение"
            ),
        ),
        migrations.AlterField(
            model_name="recipe",
            name="name",
            field=models.CharField(max_length=256, verbose_name="Название"),
        ),
        migrations.AlterModelOptions(
            name="recipeingredient",
            options={
                "default_related_name": "recipe_ingredients",
                "ordering": ("recipe", "ingredient"),
                "verbose_name": "Ингредиент рецепта",
                "verbose_name_plural": "Ингредиенты рецепта",
            },
        ),
        migrations.AlterField(
            model_name="recipeingredient",
            name="amount",
            field=models.PositiveIntegerField(
                validators=[
                    MinValueValidator(1, message="Количество не может быть меньше 1."),
                    MaxValueValidator(
                        2147483647, message="Количество не может превышать 2147483647."
                    ),
                ],
                verbose_name="Количество",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="recipeingredient",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="recipeingredient",
            constraint=models.UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_recipe_ingredient",
            ),
        ),
        migrations.AlterModelOptions(
            name="favorite",
            options={
                "default_related_name": "favorites",
                "verbose_name": "Избранный рецепт",
                "verbose_name_plural": "Избранные рецепты",
            },
        ),
        migrations.AlterUniqueTogether(
            name="favorite",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="favorite",
            name="recipe",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="menu.recipe",
                verbose_name="Рецепт",
            ),
        ),
        migrations.AlterField(
            model_name="favorite",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пользователь",
            ),
        ),
        migrations.AddConstraint(
            model_name="favorite",
            constraint=models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_favorite_user_recipe",
            ),
        ),
        migrations.AlterModelOptions(
            name="shoppingcart",
            options={
                "default_related_name": "shopping_cart_items",
                "verbose_name": "Элемент списка покупок",
                "verbose_name_plural": "Список покупок",
            },
        ),
        migrations.AlterUniqueTogether(
            name="shoppingcart",
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name="shoppingcart",
            name="recipe",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="menu.recipe",
                verbose_name="Рецепт",
            ),
        ),
        migrations.AlterField(
            model_name="shoppingcart",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пользователь",
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppingcart",
            constraint=models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_cart_user_recipe",
            ),
        ),
        migrations.AlterModelOptions(
            name="shortlinkrecipe",
            options={
                "ordering": ("-created_at",),
                "verbose_name": "Короткая ссылка",
                "verbose_name_plural": "Короткие ссылки",
            },
        ),
    ]
