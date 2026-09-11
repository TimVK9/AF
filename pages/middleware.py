from django.conf import settings
from django.shortcuts import render


class ComingSoonMiddleware:
    """
    Показывает заглушку на всех страницах, пока SITE_COMING_SOON = True.
    Админка, статика и медиа — доступны всегда.
    """

    EXEMPT_PREFIXES = (
        '/admin/',
        '/static/',
        '/media/',
        '/favicon.ico',
        '/robots.txt',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'SITE_COMING_SOON', False):
            path = request.path_info

            if not path.startswith(self.EXEMPT_PREFIXES):
                return render(request, 'coming_soon.html', status=503)

        return self.get_response(request)