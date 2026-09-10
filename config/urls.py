from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# =========================================================
# ДАШБОРД НА ГЛАВНОЙ АДМИНКИ
# =========================================================
from events.admin import admin_dashboard_callback

_original_admin_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    extra_context = extra_context or {}
    admin_dashboard_callback(request, extra_context)
    return _original_admin_index(request, extra_context)

admin.site.index = custom_admin_index
# =========================================================


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pages.urls")),      # ← статические страницы
    path("", include("events.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)