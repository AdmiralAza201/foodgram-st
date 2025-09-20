import io

from django.db.models import F, Sum
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from menu.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShortLinkRecipe,
)
from users.models import Profile, Subscription, User

from .filters import RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrAdmin
from .serializers import (
    FavoriteActionSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    SetAvatarSerializer,
    ShoppingCartActionSerializer,
    SubscriptionActionSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        query = self.request.query_params.get("name")
        queryset = Ingredient.objects.all()
        if query:
            queryset = queryset.filter(name__istartswith=query)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "ingredients"
    )
    filterset_class = RecipeFilter
    pagination_class = LimitPageNumberPagination
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "get_link"):
            return [AllowAny()]
        if self.action in (
            "create",
            "favorite",
            "shopping_cart",
            "download_shopping_cart",
        ):
            return [IsAuthenticated()]
        return [IsAuthorOrAdmin()]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        lines = self._build_shopping_lines(request.user)
        return self._file_response(lines, "shopping_list.txt")

    @staticmethod
    def _handle_post_action(request, recipe, serializer_class):
        serializer = serializer_class(
            data={},
            context={"request": request, "recipe": recipe},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = RecipeMinifiedSerializer(
            recipe,
            context={"request": request},
        ).data
        return Response(data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _handle_delete_action(request, recipe, model, error_message):
        deleted, _ = model.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {"detail": error_message},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _aggregate_shopping_items(self, user):
        base_queryset = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=user
        )
        return (
            base_queryset.values(
                name=F("ingredient__name"),
                unit=F("ingredient__measurement_unit"),
            )
            .annotate(total=Sum("amount"))
            .order_by("name")
        )

    def _build_shopping_lines(self, user):
        items = self._aggregate_shopping_items(user)
        lines = []
        for item in items:
            line = f"{item['name']} — {item['total']} {item['unit']}"
            lines.append(line)
        return lines or ["Список пуст"]

    @staticmethod
    def _file_response(lines, filename):
        content = "\n".join(lines)
        buffer = io.BytesIO(content.encode("utf-8"))
        response = FileResponse(buffer, as_attachment=True, filename=filename)
        response["Content-Type"] = "text/plain; charset=utf-8"
        return response

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method.lower() == "post":
            return self._handle_post_action(
                request,
                recipe,
                FavoriteActionSerializer,
            )
        return self._handle_delete_action(
            request,
            recipe,
            Favorite,
            "Этого рецепта не было в избранном",
        )

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method.lower() == "post":
            return self._handle_post_action(
                request,
                recipe,
                ShoppingCartActionSerializer,
            )
        return self._handle_delete_action(
            request,
            recipe,
            ShoppingCart,
            "Этого рецепта не было в корзине",
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[IsAuthenticatedOrReadOnly],
        url_path="get-link",
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        link, _ = ShortLinkRecipe.objects.get_or_create(
            recipe=recipe,
            defaults={"code": get_random_string(8)},
        )
        short_url = request.build_absolute_uri(
            reverse("short-redirect", kwargs={"code": link.code})
        )
        return Response({"short-link": short_url})


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
        serializer = self.get_serializer(page or authors, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
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


def short_redirect(request, code):
    try:
        queryset = ShortLinkRecipe.objects.select_related("recipe")
        short_link = queryset.get(code=code)
    except ShortLinkRecipe.DoesNotExist as exc:
        raise Http404 from exc
    return HttpResponseRedirect(
        reverse(
            "recipes-detail",
            kwargs={"pk": short_link.recipe.id},
        )
    )