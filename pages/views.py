from django.views.generic import TemplateView


class PrivacyView(TemplateView):
    template_name = "pages/privacy.html"


class CookiesView(TemplateView):
    template_name = "pages/cookies.html"


class TermsView(TemplateView):
    template_name = "pages/terms.html"


class AboutView(TemplateView):
    template_name = "pages/about.html"


class ContactsView(TemplateView):
    template_name = "pages/contacts.html"


class HelpView(TemplateView):
    template_name = "pages/help.html"