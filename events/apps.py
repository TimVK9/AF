from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'

    def ready(self):
        # Сигналов нет — приложение готово к работе без дополнительных импортов.
        pass