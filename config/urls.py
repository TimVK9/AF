from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import TemplateView
from events.sitemaps import EventSitemap, StaticViewSitemap


# ---------------------------------------------------------
#  Карты сайта (sitemap.xml)
# ---------------------------------------------------------
sitemaps = {
    'events': EventSitemap,
    'static': StaticViewSitemap,
}


urlpatterns = [



    # ---------------------------------------------------------
    #  Админка Django
    #  (маршрут /admin/run-import-kultisk/ удалён вместе
    #   с events/admin_views.py и моделью ImportLog)
    # ---------------------------------------------------------
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),

    # ---------------------------------------------------------
    #  Sitemap
    #  Имя короткое — удобно в reverse('sitemap').
    # ---------------------------------------------------------
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
 path('accounts/', include('allauth.urls')),

    # ---------------------------------------------------------
    #  Приложения
    #  events — первым, чтобы '' не перехватил pages.
    #  Namespace берётся из app_name в events/urls.py и pages/urls.py.
    # ---------------------------------------------------------
    path('', include('events.urls')),
    path('', include('pages.urls')),

]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)