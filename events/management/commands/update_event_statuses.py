"""
Проставляет статус FINISHED событиям, которые уже закончились.

Запуск по cron, например раз в день в 04:00:
    0 4 * * * cd /var/www/AF && /var/www/AF/.venv/bin/python \
        manage.py update_event_statuses
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event


class Command(BaseCommand):
    help = 'Помечает завершёнными события, которые уже прошли.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать, что было бы изменено',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        today = timezone.localdate()

        qs = Event.objects.filter(
            status=Event.Status.PUBLISHED,
        ).filter(
            # Событие закончилось, если end_date (или start_date) < сегодня
            # Для этого используем Coalesce в аннотации
        )

        # Разделим на две группы: с end_date и без
        with_end = Event.objects.filter(
            status=Event.Status.PUBLISHED,
            end_date__lt=today,
        )
        without_end = Event.objects.filter(
            status=Event.Status.PUBLISHED,
            end_date__isnull=True,
            start_date__lt=today,
        )

        total = with_end.count() + without_end.count()

        if dry_run:
            self.stdout.write(
                f'[DRY] Будет помечено завершёнными: {total}'
            )
            for e in with_end[:20]:
                self.stdout.write(f'  · {e.title} (до {e.end_date})')
            for e in without_end[:20]:
                self.stdout.write(f'  · {e.title} ({e.start_date})')
            return

        updated_1 = with_end.update(status=Event.Status.FINISHED)
        updated_2 = without_end.update(status=Event.Status.FINISHED)

        self.stdout.write(self.style.SUCCESS(
            f'Помечено завершёнными: {updated_1 + updated_2}'
        ))