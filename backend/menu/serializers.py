from django.conf import settings
from rest_framework import serializers

from core.fields import Base64ImageField
from menu.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient',
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'cooking_time',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_author(self, obj):
        author = obj.author
        data = {
            'email': getattr(author, 'email', ''),
            'id': author.id,
            'username': author.get_username(),
            'first_name': getattr(author, 'first_name', ''),
            'last_name': getattr(author, 'last_name', ''),
            'is_subscribed': False,
            'avatar': None,
        }
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            data['is_subscribed'] = Subscription.objects.filter(
                user=request.user,
                author=author,
            ).exists()
        profile = getattr(author, 'profile', None)
        if profile and profile.avatar:
            avatar_url = profile.avatar.url
            if request:
                data['avatar'] = request.build_absolute_uri(avatar_url)
            else:
                data['avatar'] = f"{settings.SITE_URL}{avatar_url}"
        return data

    def get_ingredients(self, obj):
        queryset = (
            RecipeIngredient.objects
            .filter(recipe=obj)
            .select_related('ingredient')
        )
        return RecipeIngredientReadSerializer(queryset, many=True).data

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        image_url = obj.image.url
        if request:
            return request.build_absolute_uri(image_url)
        return f"{settings.SITE_URL}{image_url}"

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return obj.favorited_by.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return obj.in_carts.filter(user=user).exists()
        return False


class FavoriteActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ()

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = self.context['recipe']
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном')
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = self.context['recipe']
        return Favorite.objects.create(user=user, recipe=recipe)


class ShoppingCartActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ()

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = self.context['recipe']
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в корзине')
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        recipe = self.context['recipe']
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
            'name',
            'image',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
        )

    def validate(self, attrs):
        ingredients = attrs.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': ['Это поле не может быть пустым.']}
            )
        seen = set()
        for item in ingredients:
            ingredient = item['ingredient']
            if ingredient.id in seen:
                raise serializers.ValidationError('Duplicate ingredient')
            seen.add(ingredient.id)
        if attrs['cooking_time'] < 1:
            raise serializers.ValidationError('cooking_time must be >=1')
        return attrs

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data,
        )
        if tags:
            recipe.tags.set(tags)
        bulk = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount'],
            )
            for item in ingredients
        ]
        RecipeIngredient.objects.bulk_create(bulk)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags or [])
        if ingredients is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            bulk = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=item['ingredient'],
                    amount=item['amount'],
                )
                for item in ingredients
            ]
            RecipeIngredient.objects.bulk_create(bulk)
        return instance


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        image_url = obj.image.url
        if request:
            return request.build_absolute_uri(image_url)
        return f"{settings.SITE_URL}{image_url}"
