"""URL-маршруты приложения events."""
from django.urls import path

from . import views

app_name = 'events'

urlpatterns = [
    # Публичные страницы
    path('', views.EventList.as_view(), name='home'),
    path('event/<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    path('place/<slug:slug>/', views.PlaceDetailView.as_view(), name='place_detail'),

    # Управление (staff)
    path('manage/events/', views.EventManageListView.as_view(), name='event_list_manage'),
    path('manage/events/new/', views.EventCreateView.as_view(), name='event_create'),
    path('manage/events/<slug:slug>/edit/', views.EventUpdateView.as_view(), name='event_update'),
    path('manage/events/bulk/', views.EventBulkActionView.as_view(), name='event_bulk'),
]