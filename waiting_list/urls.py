from django.urls import path
from . import views

app_name = 'waiting_list'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('submit/', views.submit_interest, name='submit_interest'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
]
