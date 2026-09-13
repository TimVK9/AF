"""
Корневые URL проекта.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from events import admin_views
from events import views_auth


urlpatterns = [
    # ---------------------------------------------------------
    # Служебные админские вью — ДО admin.site.urls,
    # чтобы перехватывать /admin/... до стандартной админки
    # ---------------------------------------------------------
    path(
        'admin/run-import-kultisk/',
        admin_views.run_import_kultisk,
        name='run_import_kultisk',
    ),

    # ---------------------------------------------------------
    # Админка
    # ---------------------------------------------------------
    path('admin/', admin.site.urls),

    # ---------------------------------------------------------
    # Своя авторизация с 2FA — в корне, без namespace
    # ---------------------------------------------------------
    path('login/',  views_auth.login_view,      name='login'),
    path('verify/', views_auth.verify_view,     name='verify'),
    path('resend/', views_auth.resend_otp_view, name='resend_otp'),
    path('logout/', views_auth.logout_view,     name='logout'),

    # ---------------------------------------------------------
    # Приложения
    # ---------------------------------------------------------
    path('', include('events.urls')),
    path('', include('pages.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)