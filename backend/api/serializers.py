from django.conf import settings
from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField

from core.constants import (
    COOKING_TIME_MAX,
    COOKING_TIME_MIN,
    INGREDIENT_AMOUNT_MIN,
    INGREDIENT_AMOUNT_MAX,
)
from menu.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.serializers import UserSerializer


class ImageUrlMixin:
    def _build_image_url(self, image):
        if not image:
            return ""
        request = self.context.get("request")
        url = image.url
        if request:
            return request.build_absolute_uri(url)
        return f"{settings.SITE_URL}{url}"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
    )
    amount = serializers.IntegerField(
        min_value=INGREDIENT_AMOUNT_MIN,
        max_value=INGREDIENT_AMOUNT_MAX,
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "amount")


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="ingredient.id")
    name = serializers.CharField(source="ingredient.name")
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit",
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeReadSerializer(ImageUrlMixin, serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source="recipe_ingredients",
        many=True,
        read_only=True,
    )
    image = serializers.ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "image",
            "text",
            "cooking_time",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, obj):
        return self._is_user_related(obj, "favorites")

    def get_is_in_shopping_cart(self, obj):
        return self._is_user_related(obj, "shopping_cart_items")

    def _is_user_related(self, obj, manager_name: str) -> bool:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        manager = getattr(obj, manager_name)
        is_authenticated = bool(user and user.is_authenticated)
        return bool(is_authenticated and manager.filter(user=user).exists())

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["image"] = self._build_image_url(instance.image)
        return representation


class FavoriteActionSerializer(serializers.Serializer):
    def validate(self, attrs):
        user = self.context["request"].user
        recipe = self.context["recipe"]
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в избранном")
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        recipe = self.context["recipe"]
        return Favorite.objects.create(user=user, recipe=recipe)


class ShoppingCartActionSerializer(serializers.Serializer):
    def validate(self, attrs):
        user = self.context["request"].user
        recipe = self.context["recipe"]
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Рецепт уже в корзине")
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        recipe = self.context["recipe"]
        return ShoppingCart.objects.create(user=user, recipe=recipe)


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
    )
    ingredients = RecipeIngredientWriteSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            "name",
            "image",
            "text",
            "cooking_time",
            "tags",
            "ingredients",
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Это поле не может быть пустым.")
        return value

    def validate(self, attrs):
        ingredients = attrs.get("ingredients")
        if ingredients is None:
            raise serializers.ValidationError(
                {"ingredients": ["Это поле не может быть пустым."]}
            )
        elif not ingredients:
            raise serializers.ValidationError(
                {"ingredients": ["Это поле не может быть пустым."]}
            )
        else:
            ingredient_ids = [item["ingredient"].id for item in ingredients]
            has_duplicates = len(ingredient_ids) != len(set(ingredient_ids))
            if has_duplicates:
                duplicates_message = "Ингредиенты не должны повторяться."
                raise serializers.ValidationError(duplicates_message)

        cooking_time = attrs.get(
            "cooking_time",
            getattr(self.instance, "cooking_time", None),
        )
        if cooking_time is None:
            raise serializers.ValidationError(
                {"cooking_time": ["Это поле не может быть пустым."]}
            )
        if cooking_time < COOKING_TIME_MIN:
            message_min = (
                "Время приготовления не может быть меньше {value} мин.".format(
                    value=COOKING_TIME_MIN
                )
            )
            raise serializers.ValidationError(message_min)
        if cooking_time > COOKING_TIME_MAX:
            template = "Время приготовления не может превышать {value} мин."
            message_max = template.format(value=COOKING_TIME_MAX)
            raise serializers.ValidationError(message_max)
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)
        if tags:
            recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("ingredients")
        instance = super().update(instance, validated_data)
        if tags is not None:
            instance.tags.set(tags or [])
        instance.recipe_ingredients.all().delete()
        self._set_ingredients(instance, ingredients)
        return instance

    @staticmethod
    def _set_ingredients(recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=item["ingredient"],
                    amount=item["amount"],
                )
                for item in ingredients
            ]
        )

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context,
        ).data


class RecipeMinifiedSerializer(ImageUrlMixin, serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["image"] = self._build_image_url(instance.image)
        return representation
