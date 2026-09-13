"""
Удаляет старые записи аналитики.

Запуск по cron, например раз в месяц:
    0 4 1 * * cd /var/www/AF && /var/www/AF/.venv/bin/python \
        manage.py purge_old_views
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from events.models import EventView, PlaceView, CategoryView, SiteView


class Command(BaseCommand):
    help = 'Удаляет записи аналитики старше N дней.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Сколько дней хранить (по умолчанию 365)',
        )

    def handle(self, *args, **options):
        days = options['days']
        since = timezone.localdate() - timedelta(days=days)

        total = 0
        for model in (EventView, PlaceView, CategoryView, SiteView):
            deleted, _ = model.objects.filter(date__lt=since).delete()
            total += deleted
            self.stdout.write(f'{model.__name__}: удалено {deleted}')

        self.stdout.write(self.style.SUCCESS(f'Всего удалено: {total}'))