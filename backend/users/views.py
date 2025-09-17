from django.contrib.auth import get_user_model
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from menu.pagination import LimitPageNumberPagination
from users.models import Profile, Subscription
from users.serializers import (
    SetAvatarSerializer,
    SetPasswordSerializer,
    SubscriptionSerializer,
    TokenCreateSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)

User = get_user_model()


class UserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all().order_by('id')
    permission_classes = [AllowAny]
    pagination_class = LimitPageNumberPagination
    authentication_classes = [TokenAuthentication]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        Profile.objects.get_or_create(user=request.user)
        serializer = UserSerializer(
            request.user,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        authors = (
            User.objects
            .filter(subscribers__user=request.user)
            .order_by('id')
        )
        page = self.paginate_queryset(authors)
        serializer_context = {'request': request}
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page,
                many=True,
                context=serializer_context,
            )
            return self.get_paginated_response(serializer.data)
        serializer = UserWithRecipesSerializer(
            authors,
            many=True,
            context=serializer_context,
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, pk=None):
        try:
            author = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.method.lower() == 'post':
            serializer = SubscriptionSerializer(
                data={},
                context={'request': request, 'author': author},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response_serializer = UserWithRecipesSerializer(
                author,
                context={'request': request},
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Не были подписаны'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password',
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_password = serializer.validated_data['current_password']
        if not request.user.check_password(current_password):
            return Response(
                {'current_password': ['Неверный пароль']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar',
    )
    def avatar(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        if request.method.lower() == 'delete':
            if profile.avatar:
                profile.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = SetAvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile.avatar = serializer.validated_data['avatar']
        profile.save()
        avatar_url = request.build_absolute_uri(profile.avatar.url)
        return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)


class TokenLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Неверные учетные данные'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.check_password(password):
            return Response(
                {'detail': 'Неверные учетные данные'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key}, status=status.HTTP_200_OK)


class TokenLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
