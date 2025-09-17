import base64
import binascii
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from menu.models import Ingredient, Recipe, RecipeIngredient, Tag


def _get(obj, *keys, default=None):
    for key in keys:
        if key in obj:
            return obj[key]
    return default


class Command(BaseCommand):
    help = (
        "Load tags, ingredients, recipes from data/*.json"
        " (supports multiple schemas)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            default='data',
            help='Path to data directory',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        base_dir = Path(options['dir'])
        user_model = get_user_model()

        demo_users = (
            ('demo1', 'demo1@example.com'),
            ('demo2', 'demo2@example.com'),
        )
        for username, email in demo_users:
            user, _ = user_model.objects.get_or_create(
                username=username,
                defaults={'email': email},
            )
            if not user.has_usable_password():
                user.set_password('demo12345')
                user.save()

        self._load_tags(base_dir)
        self._load_ingredients(base_dir)
        self._load_recipes(base_dir, user_model)
        self.stdout.write(self.style.SUCCESS(f"Loaded data from {base_dir}"))

    def _load_tags(self, base_dir: Path):
        path = base_dir / 'tags.json'
        if not path.exists():
            return
        items = json.loads(path.read_text(encoding='utf-8'))
        for item in items:
            slug = _get(item, 'slug')
            name = _get(item, 'name', 'title')
            color = _get(item, 'color', default='#FFFFFF')
            if slug and name:
                Tag.objects.get_or_create(
                    slug=slug,
                    defaults={'name': name, 'color': color},
                )

    def _load_ingredients(self, base_dir: Path):
        path = base_dir / 'ingredients.json'
        if not path.exists():
            return
        items = json.loads(path.read_text(encoding='utf-8'))
        for item in items:
            name = _get(item, 'name', 'title')
            unit = _get(item, 'measurement_unit', 'dimension', default='')
            if name and unit:
                Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=unit,
                )

    def _load_recipes(self, base_dir: Path, user_model):
        path = base_dir / 'recipes.json'
        if not path.exists():
            return
        items = json.loads(path.read_text(encoding='utf-8'))
        for item in items:
            username = _get(item, 'author_username', default='demo1')
            author = user_model.objects.get(username=username)
            recipe, _ = Recipe.objects.get_or_create(
                author=author,
                name=_get(item, 'name', 'title', default='Рецепт'),
                defaults={
                    'text': _get(item, 'text', 'description', default=''),
                    'cooking_time': int(
                        _get(item, 'cooking_time', 'time', default=10)
                    ),
                },
            )
            self._load_recipe_image(recipe, item)
            self._load_recipe_tags(recipe, item)
            self._load_recipe_ingredients(recipe, item)

    def _load_recipe_image(self, recipe, item):
        encoded = _get(item, 'image_base64')
        if not encoded or recipe.image:
            return
        try:
            content = base64.b64decode(encoded)
        except (TypeError, ValueError, binascii.Error):
            return
        recipe.image.save('img.png', ContentFile(content), save=True)

    def _load_recipe_tags(self, recipe, item):
        slugs = _get(item, 'tags', default=[])
        if slugs:
            recipe.tags.set(list(Tag.objects.filter(slug__in=slugs)))

    def _load_recipe_ingredients(self, recipe, item):
        ingredients = _get(item, 'ingredients', default=[])
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        for ingredient_data in ingredients:
            ingredient = self._resolve_ingredient(ingredient_data)
            amount = int(_get(ingredient_data, 'amount', default=1))
            if ingredient:
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount,
                )

    def _resolve_ingredient(self, data):
        name = _get(data, 'name')
        if name:
            return Ingredient.objects.filter(name=name).first()
        ingredient_id = _get(data, 'id')
        if ingredient_id is not None:
            return Ingredient.objects.filter(id=ingredient_id).first()
        return None
