from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, TokenLoginView, TokenLogoutView

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', TokenLoginView.as_view()),
    path('auth/token/logout/', TokenLogoutView.as_view()),
]
