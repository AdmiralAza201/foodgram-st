from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.pagination import LimitPageNumberPagination
from users.models import Profile, Subscription, User
from users.serializers import (
    SetAvatarSerializer,
    SubscriptionActionSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all().order_by("email")
    pagination_class = LimitPageNumberPagination
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.action in ("me", "subscriptions", "subscribe", "avatar"):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "subscriptions":
            return UserWithRecipesSerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request, *args, **kwargs):
        authors = User.objects.filter(
            subscribers__user=request.user,
        ).order_by("email")
        page = self.paginate_queryset(authors)
        serializer_class = self.get_serializer_class()
        serializer_kwargs = {
            "many": True,
            "context": self.get_serializer_context(),
        }
        if page is not None:
            serializer = serializer_class(page, **serializer_kwargs)
            return self.get_paginated_response(serializer.data)
        serializer = serializer_class(authors, **serializer_kwargs)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, *args, **kwargs):
        author = self.get_object()
        if request.method.lower() == "post":
            serializer = SubscriptionActionSerializer(
                data={},
                context={"request": request, "author": author},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = UserWithRecipesSerializer(
                author,
                context=self.get_serializer_context(),
            ).data
            return Response(data, status=status.HTTP_201_CREATED)
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if not deleted:
            return Response(
                {"detail": "Не были подписаны"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["put", "delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if request.method.lower() == "delete":
            if profile.avatar:
                profile.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = SetAvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.avatar = serializer.validated_data["avatar"]
        profile.save(update_fields=["avatar"])
        avatar_url = request.build_absolute_uri(profile.avatar.url)
        return Response({"avatar": avatar_url}, status=status.HTTP_200_OK)
