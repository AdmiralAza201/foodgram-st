from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.conf import settings
from users.models import Profile, Subscription
from core.fields import Base64ImageField
from menu.models import Recipe
from rest_framework.validators import ValidationError

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                author=obj,
            ).exists()
        return False

    def get_avatar(self, obj):
        prof = getattr(obj, 'profile', None)
        if not prof or not prof.avatar:
            return None
        request = self.context.get('request')
        url = prof.avatar.url
        if request:
            return request.build_absolute_uri(url)
        return f"{settings.SITE_URL}{url}"


class UserCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, max_length=254)
    username = serializers.RegexField(
        r'^[\w.@+-]+\Z',
        required=True,
        max_length=150,
    )
    first_name = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=150,
    )
    last_name = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=150,
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким email уже существует'
            )
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                'Пользователь с таким username уже существует'
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        Profile.objects.get_or_create(user=user)
        return user

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'username': instance.get_username(),
            'first_name': instance.first_name or '',
            'last_name': instance.last_name or '',
            'email': instance.email or '',
        }


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        qs = Recipe.objects.filter(author=obj)
        limit = None
        request = self.context.get('request')
        if request:
            try:
                limit = int(request.query_params.get('recipes_limit'))
            except (TypeError, ValueError):
                pass

        def _item(r):
            url = None
            if r.image:
                current_request = self.context.get('request')
                url = r.image.url
                if current_request:
                    url = current_request.build_absolute_uri(url)
                else:
                    url = f"{settings.SITE_URL}{url}"
            return {
                'id': r.id,
                'name': r.name,
                'image': url,
                'cooking_time': r.cooking_time,
            }
        data = [_item(r) for r in qs]
        if isinstance(limit, int) and limit >= 0:
            return data[:limit]
        return data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class TokenCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    auth_token = serializers.CharField()


class SetPasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()


class SetAvatarSerializer(serializers.Serializer):
    avatar = Base64ImageField()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ()

    def validate(self, attrs):
        request = self.context['request']
        author = self.context['author']
        if author == request.user:
            raise ValidationError('Нельзя подписаться на себя')
        if Subscription.objects.filter(
            user=request.user,
            author=author,
        ).exists():
            raise ValidationError('Уже подписаны')
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        author = self.context['author']
        return Subscription.objects.create(
            user=request.user,
            author=author,
        )
