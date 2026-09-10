from django.urls import path
from . import views



urlpatterns = [
    # Главная
    path('', views.EventList.as_view(), name='home'),
    path('event/<slug:slug>/', views.EventDetailView.as_view(), name='event_detail',),
    
    
   
]

