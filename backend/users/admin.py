from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Profile, Subscription

User = get_user_model()


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'avatar')
    search_fields = ('user__username', 'user__email')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created_at')
    search_fields = (
        'user__username',
        'author__username',
        'user__email',
        'author__email',
    )
