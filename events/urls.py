"""URL-маршруты приложения events."""
from django.urls import path

from . import views
from . import feeds

app_name = 'events'

urlpatterns = [
    # Публичные страницы
    path('', views.EventList.as_view(), name='home'),
    path('event/<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    path('place/<slug:slug>/', views.PlaceDetailView.as_view(), name='place_detail'),

    # RSS-фиды
    path('rss/', feeds.LatestEventsFeed(), name='rss'),
    path('rss/category/<slug:slug>/', feeds.CategoryEventsFeed(), name='rss_category'),
    path('rss/place/<slug:slug>/', feeds.PlaceEventsFeed(), name='rss_place'),

    # Управление (staff)
    path('manage/events/', views.EventManageListView.as_view(), name='event_list_manage'),
    path('manage/events/new/', views.EventCreateView.as_view(), name='event_create'),
    path('manage/events/<slug:slug>/edit/', views.EventUpdateView.as_view(), name='event_update'),
    path('manage/events/bulk/', views.EventBulkActionView.as_view(), name='event_bulk'),
]