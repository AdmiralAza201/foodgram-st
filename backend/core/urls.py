from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from menu.views import short_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('menu.urls')),
    path('api/', include('users.urls')),
    re_path(
        r'^s/(?P<code>[A-Za-z0-9_-]+)/?$',
        short_redirect,
        name='short-redirect',
    ),
]

# Отдаём /media/ силами Django ТОЛЬКО в dev.
# В проде /media/ обслуживает Nginx.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
    # опционально для статических файлов apps в dev:
    # from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    # urlpatterns += staticfiles_urlpatterns()
