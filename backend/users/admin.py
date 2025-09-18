from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _

from .models import Profile, Subscription, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Personal info"),
            {"fields": ("first_name", "last_name", "username")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )
    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "recipes_count",
        "subscribers_count",
        "is_active",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    ordering = ("email",)
    search_fields = ("email", "username", "first_name", "last_name")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            recipes_total=Count("recipes", distinct=True),
            subscribers_total=Count("subscribers", distinct=True),
        )

    @admin.display(description="Рецептов")
    def recipes_count(self, obj):
        return obj.recipes_total

    @admin.display(description="Подписчиков")
    def subscribers_count(self, obj):
        return obj.subscribers_total


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "avatar")
    search_fields = ("user__email", "user__username")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "author", "created_at")
    search_fields = (
        "user__email",
        "user__username",
        "author__email",
        "author__username",
    )
    list_filter = ("created_at",)
