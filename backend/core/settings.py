import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

from .constants import (
    DEFAULT_ALLOWED_HOSTS,
    DEFAULT_CSRF_TRUSTED_ORIGINS,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SQLITE_DB_NAME,
)

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()


def get_list_from_env(env_name: str, default_value: str) -> list[str]:

    return [
        item.strip()
        for item in os.getenv(env_name, default_value).split(",")
        if item.strip()
    ]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", get_random_secret_key())
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = get_list_from_env("ALLOWED_HOSTS", DEFAULT_ALLOWED_HOSTS)
CSRF_TRUSTED_ORIGINS = get_list_from_env(
    "CSRF_TRUSTED_ORIGINS", DEFAULT_CSRF_TRUSTED_ORIGINS
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "djoser",
    "api",
    "menu",
    "users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

USE_SQLITE = os.getenv("DJANGO_USE_SQLITE")

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / os.getenv("SQLITE_DB_NAME", DEFAULT_SQLITE_DB_NAME),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "foodgram"),
            "USER": os.getenv("POSTGRES_USER", "foodgram"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "foodgram"),
            "HOST": os.getenv("POSTGRES_HOST", "db"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": DEFAULT_PAGE_SIZE,
}


SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1")

AUTH_USER_MODEL = "users.User"

DJOSER = {
    "LOGIN_FIELD": "email",
    "SERIALIZERS": {
        "user": "users.serializers.UserSerializer",
        "current_user": "users.serializers.UserSerializer",
    },
    "PERMISSIONS": {
        "user_list": ["rest_framework.permissions.AllowAny"],
        "user": ["rest_framework.permissions.AllowAny"],
        "current_user": ["rest_framework.permissions.IsAuthenticated"],
        "user_delete": ["rest_framework.permissions.IsAdminUser"],
    },
}
