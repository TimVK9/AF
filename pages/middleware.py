"""
Middleware «Скоро запуск».

Если SiteSettings.coming_soon = True, все не-админы видят заглушку.
Админы (is_staff или is_superuser) видят сайт как обычно.

Значение хранится в БД (модель SiteSettings) и меняется через админку —
перезапуск Gunicorn не требуется.
"""

from django.shortcuts import render


class ComingSoonMiddleware:
    """
    Заглушка для не-админов при включённом режиме «Скоро запуск».
    """
    EXEMPT_PREFIXES = (
        '/admin/',
        '/static/',
        '/media/',
        '/login/',
        '/logout/',
        '/verify/',
        '/resend/',
        '/sitemap.xml',
        '/robots.txt',
        '/favicon.ico',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Пропускаем пути из белого списка
        if request.path_info.startswith(self.EXEMPT_PREFIXES):
            return self.get_response(request)

        # Админы и суперюзеры видят сайт всегда
        if request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        ):
            return self.get_response(request)

        # Читаем настройки из БД
        try:
            from events.models import SiteSettings
            settings_obj = SiteSettings.load()
            if settings_obj.coming_soon:
                return render(
                    request,
                    'coming_soon.html',
                    {'message': settings_obj.coming_soon_message},
                    status=503,
                )
        except Exception:
            # Если модель ещё не мигрирована или что-то упало —
            # не роняем сайт, просто пропускаем
            pass

        return self.get_response(request)