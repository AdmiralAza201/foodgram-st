from django.conf import settings
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField

from core.constants import (
    COOKING_TIME_MAX,
    COOKING_TIME_MAX_MESSAGE,
    COOKING_TIME_MIN,
    COOKING_TIME_MIN_MESSAGE,
    INGREDIENT_AMOUNT_MAX,
    INGREDIENT_AMOUNT_MIN,
)
from menu.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
)
from users.models import Profile, Subscription, User


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


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = DjoserUserSerializer.Meta.fields + ("is_subscribed", "avatar")

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and obj.subscribers.filter(user=request.user).exists()
        )

    def get_avatar(self, obj):
        if not isinstance(obj, User):
            return None

        try:
            profile = obj.profiles
        except (Profile.DoesNotExist, AttributeError):
            profile = None
        if not profile or not profile.avatar:
            return None
        request = self.context.get("request")
        url = profile.avatar.url
        if request:
            return request.build_absolute_uri(url)
        return f"{settings.SITE_URL}{url}"


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source="recipe_ingredients",
        many=True,
        read_only=True,
    )
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
        return self._is_user_related(obj, "shopping_carts")

    def _is_user_related(self, obj, manager_name: str) -> bool:
        request = self.context.get("request")
        user = getattr(request, "user", None)
        manager = getattr(obj, manager_name)
        is_authenticated = bool(user and user.is_authenticated)
        return bool(is_authenticated and manager.filter(user=user).exists())


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
    ingredients = RecipeIngredientWriteSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            "name",
            "image",
            "text",
            "cooking_time",
            "ingredients",
        )

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Это поле не может быть пустым.")
        return value

    def validate(self, attrs):
        ingredients = attrs.get("ingredients")
        if ingredients is None or not ingredients:
            raise serializers.ValidationError(
                {"ingredients": ["Это поле не может быть пустым."]}
            )

        ingredient_ids = [item["ingredient"].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": ["Ингредиенты не должны повторяться."]}
            )

        cooking_time = attrs.get("cooking_time")
        if cooking_time is None and self.instance is not None:
            cooking_time = self.instance.cooking_time
        if cooking_time is None:
            raise serializers.ValidationError(
                {"cooking_time": ["Это поле не может быть пустым."]}
            )
        if cooking_time < COOKING_TIME_MIN:
            raise serializers.ValidationError(
                {
                    "cooking_time": [
                        COOKING_TIME_MIN_MESSAGE.format(value=COOKING_TIME_MIN)
                    ]
                }
            )
        if cooking_time > COOKING_TIME_MAX:
            raise serializers.ValidationError(
                {
                    "cooking_time": [
                        COOKING_TIME_MAX_MESSAGE.format(value=COOKING_TIME_MAX)
                    ]
                }
            )
        return attrs

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients", [])
        recipe = Recipe.objects.create(**validated_data)
        self._set_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients")
        instance.recipe_ingredients.all().delete()
        self._set_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

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


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        recipes_qs = obj.recipes.all()
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit") if request else None
        try:
            limit_value = int(limit) if limit is not None else None
        except (TypeError, ValueError):
            limit_value = None
        if limit_value is not None and limit_value >= 0:
            recipes_qs = recipes_qs[:limit_value]
        serializer = RecipeMinifiedSerializer(
            recipes_qs,
            many=True,
            context=self.context,
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SetAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()


class SubscriptionActionSerializer(serializers.Serializer):
    def validate(self, attrs):
        request = self.context["request"]
        author = self.context["author"]
        if author == request.user:
            raise serializers.ValidationError("Нельзя подписаться на себя")
        if author.subscribers.filter(user=request.user).exists():
            raise serializers.ValidationError("Уже подписаны")
        return attrs

    def save(self, **kwargs):
        request = self.context["request"]
        author = self.context["author"]
        return Subscription.objects.create(user=request.user, author=author)
