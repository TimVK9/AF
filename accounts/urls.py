from django.urls import path
from . import views

app_name = 'accounts'


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('verify/', views.verify_view, name='verify'),
    path('resend/', views.resend_otp_view, name='resend_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('legal/privacy/', views.legal_document_view, {'doc_type': 'privacy'}, name='legal_privacy'),
    path('legal/terms/', views.legal_document_view, {'doc_type': 'terms'}, name='legal_terms'),
   
]