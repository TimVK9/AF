from django.urls import path

from . import views


app_name = "pages"


urlpatterns = [
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    path("cookies/", views.CookiesView.as_view(), name="cookies"),
    path("terms/", views.TermsView.as_view(), name="terms"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("contacts/", views.ContactsView.as_view(), name="contacts"),
    path("help/", views.HelpView.as_view(), name="help"),
]