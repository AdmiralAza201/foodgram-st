from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from core.constants import (
    USER_FIRST_NAME_MAX_LENGTH,
    USER_LAST_NAME_MAX_LENGTH,
    USERNAME_HELP_TEXT_TEMPLATE,
    USERNAME_MAX_LENGTH,
)


class User(AbstractUser):
    username = models.CharField(
        _("username"),
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        help_text=_(
            USERNAME_HELP_TEXT_TEMPLATE.format(limit_value=USERNAME_MAX_LENGTH)
        ),
        validators=[AbstractUser.username_validator],
        error_messages={
            "unique": _("Пользователь с таким username уже существует."),
        },
    )
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(
        _("first name"),
        max_length=USER_FIRST_NAME_MAX_LENGTH,
    )
    last_name = models.CharField(
        _("last name"),
        max_length=USER_LAST_NAME_MAX_LENGTH,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ("email",)
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str:
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profiles",
        verbose_name="Пользователь",
    )
    avatar = models.ImageField(
        upload_to="users/",
        blank=True,
        null=True,
        verbose_name="Аватар",
    )

    class Meta:
        ordering = ("user__email",)
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self) -> str:
        return f"Профиль {self.user}"


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создана",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "author"),
                name="unique_subscription_user_author",
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="no_self_subscription",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user} -> {self.author}"


@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
