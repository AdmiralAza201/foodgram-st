import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from menu.models import Ingredient, Recipe, RecipeIngredient, Tag


_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
    "AAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJR"
    "U5ErkJggg=="
)
_PNG_CONTENT = base64.b64decode(_PNG_BASE64)


_TAGS = (
    ("breakfast", "Завтрак", "#E26C2D"),
    ("lunch", "Обед", "#49B64E"),
    ("dinner", "Ужин", "#8775D2"),
)

_INGREDIENTS = (
    ("Мука", "г"),
    ("Яйцо", "шт"),
    ("Молоко", "мл"),
)


class Command(BaseCommand):
    help = "Create demo users/recipes/tags/ingredients"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        users = self._ensure_demo_users()
        self._ensure_tags()
        ingredients = self._ensure_ingredients()
        self._ensure_recipes(users, ingredients)
        self.stdout.write(self.style.SUCCESS("Demo created"))

    def _ensure_demo_users(self):
        user_model = get_user_model()
        demo_users = {}
        for username in ("demo1", "demo2"):
            defaults = {"email": f"{username}@example.com"}
            user, _ = user_model.objects.get_or_create(
                username=username,
                defaults=defaults,
            )
            if not user.has_usable_password():
                user.set_password("demo12345")
                user.save()
            demo_users[username] = user
        return demo_users

    def _ensure_tags(self):
        for slug, name, color in _TAGS:
            Tag.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "color": color},
            )

    def _ensure_ingredients(self):
        created = {}
        for name, unit in _INGREDIENTS:
            ingredient, _ = Ingredient.objects.get_or_create(
                name=name,
                measurement_unit=unit,
            )
            created[name] = ingredient
        return created

    def _ensure_recipes(self, users, ingredients):
        demo_data = (
            (
                users["demo1"],
                "Блинчики",
                "Тонкие блины",
                15,
                ("Мука", 200),
                ("Молоко", 300),
                ("Яйцо", 2),
            ),
            (
                users["demo2"],
                "Омлет",
                "Классический омлет",
                10,
                ("Яйцо", 3),
                ("Молоко", 50),
            ),
        )

        for author, name, text, time_minutes, *ingredient_specs in demo_data:
            recipe, _ = Recipe.objects.get_or_create(
                author=author,
                name=name,
                defaults={
                    "text": text,
                    "cooking_time": time_minutes,
                },
            )
            if not recipe.image:
                recipe.image.save(
                    "1x1.png",
                    ContentFile(_PNG_CONTENT),
                    save=True,
                )

            tag_qs = Tag.objects.all()
            if name == "Блинчики":
                recipe.tags.set(tag_qs[:2])
            else:
                recipe.tags.set(tag_qs[1:])

            for ingredient_name, amount in ingredient_specs:
                RecipeIngredient.objects.get_or_create(
                    recipe=recipe,
                    ingredient=ingredients[ingredient_name],
                    defaults={"amount": amount},
                )
