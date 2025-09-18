from django.conf import settings
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField

from .models import Profile, Subscription, User


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

        profile = getattr(obj, "profile", None)
        if profile is None:
            try:
                profile = Profile.objects.get(user=obj)
            except Profile.DoesNotExist:
                return None
            except AttributeError:
                return None
        if not profile or not profile.avatar:
            return None
        request = self.context.get("request")
        url = profile.avatar.url
        if request:
            return request.build_absolute_uri(url)
        return f"{settings.SITE_URL}{url}"


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, obj):
        from api.serializers import RecipeMinifiedSerializer

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
            context={"request": request},
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
