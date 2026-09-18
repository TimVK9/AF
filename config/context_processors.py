from django.conf import settings


def metrika_context(request):
    return {
        "YANDEX_METRIKA_ID": getattr(settings, "YANDEX_METRIKA_ID", None),
    }
