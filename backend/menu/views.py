import io
from csv import writer as csv_writer

from django.conf import settings
from django.db.models import F, Sum
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.utils.crypto import get_random_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    ShortLinkRecipe,
    Tag,
)
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrAdmin
from .serializers import (
    FavoriteActionSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShoppingCartActionSerializer,
    TagSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        query = self.request.query_params.get('name')
        queryset = Ingredient.objects.all()
        if query:
            queryset = queryset.filter(name__istartswith=query)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (
        Recipe.objects.all()
        .select_related('author')
        .prefetch_related('tags', 'ingredients')
    )
    filterset_class = RecipeFilter
    pagination_class = LimitPageNumberPagination
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend]

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'get_link'):
            return [AllowAny()]
        if self.action in (
            'create',
            'favorite',
            'shopping_cart',
            'download_shopping_cart',
            'export',
        ):
            return [IsAuthenticated()]
        return [IsAuthorOrAdmin()]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def export(self, request):
        queryset = self.get_queryset().filter(author=request.user)
        buffer = io.StringIO()
        writer = csv_writer(buffer)
        writer.writerow(['id', 'name', 'cooking_time', 'tags', 'ingredients'])
        for recipe in queryset:
            tags = ','.join(recipe.tags.values_list('slug', flat=True))
            ingredients = []
            recipe_items = (
                RecipeIngredient.objects
                .filter(recipe=recipe)
                .select_related('ingredient')
            )
            for item in recipe_items:
                measurement = item.ingredient.measurement_unit
                ingredients.append(
                    f"{item.ingredient.name}:{item.amount}{measurement}"
                )
            writer.writerow(
                [
                    recipe.id,
                    recipe.name,
                    recipe.cooking_time,
                    tags,
                    ' | '.join(ingredients),
                ]
            )
        content = buffer.getvalue()
        response = HttpResponse(
            content,
            content_type='text/csv; charset=utf-8',
        )
        response['Content-Disposition'] = 'attachment; filename=recipes.csv'
        return response

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        if request.method.lower() == 'post':
            serializer = FavoriteActionSerializer(
                data={},
                context={'request': request, 'recipe': recipe},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = RecipeMinifiedSerializer(
                recipe,
                context={'request': request},
            ).data
            return Response(data, status=status.HTTP_201_CREATED)
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Этого рецепта не было в избранном'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        if request.method.lower() == 'post':
            serializer = ShoppingCartActionSerializer(
                data={},
                context={'request': request, 'recipe': recipe},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = RecipeMinifiedSerializer(
                recipe,
                context={'request': request},
            ).data
            return Response(data, status=status.HTTP_201_CREATED)
        deleted, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Этого рецепта не было в корзине'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        if 'ingredients' not in request.data:
            return Response(
                {'ingredients': ['Обязательное поле.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        kwargs['partial'] = True
        instance = self.get_object()
        serializer = RecipeWriteSerializer(
            instance,
            data=request.data,
            context={'request': request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = RecipeReadSerializer(
            instance,
            context={'request': request},
        )
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = RecipeWriteSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read_serializer = RecipeReadSerializer(
            instance,
            context={'request': request},
        )
        headers = self.get_success_headers(read_serializer.data)
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = False
        instance = self.get_object()
        serializer = RecipeWriteSerializer(
            instance,
            data=request.data,
            context={'request': request},
            partial=False,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        read_serializer = RecipeReadSerializer(
            instance,
            context={'request': request},
        )
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        items = (
            RecipeIngredient.objects
            .filter(recipe__in_carts__user=request.user)
            .values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit'),
            )
            .annotate(total=Sum('amount'))
            .order_by('name')
        )
        lines = [
            f"{item['name']} — {item['total']} {item['unit']}"
            for item in items
        ]
        response = HttpResponse(
            '\n'.join(lines) or 'Список пуст',
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename=shopping_list.txt'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[IsAuthenticatedOrReadOnly],
        url_path='get-link',
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        link, _ = ShortLinkRecipe.objects.get_or_create(
            recipe=recipe,
            defaults={'code': get_random_string(8)},
        )
        site = getattr(settings, 'SITE_URL', 'http://localhost')
        return Response({'short-link': f"{site}/s/{link.code}"})


def short_redirect(request, code):
    try:
        short_link = (
            ShortLinkRecipe.objects
            .select_related('recipe')
            .get(code=code)
        )
    except ShortLinkRecipe.DoesNotExist as exc:
        raise Http404 from exc
    return HttpResponseRedirect(f"/recipes/{short_link.recipe.id}")
