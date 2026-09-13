from django.apps import AppConfig
from django.contrib import admin


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'

    def ready(self):
        from .admin import admin_dashboard_callback

        _original_index = admin.site.index

        def custom_index(request, extra_context=None):
            extra_context = extra_context or {}
            admin_dashboard_callback(request, extra_context)
            return _original_index(request, extra_context)

        admin.site.index = custom_index