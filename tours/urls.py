from django.urls import path
from . import views

urlpatterns = [
    path('iskitim/', views.iskitim_events, name='iskitim_events'),
]
