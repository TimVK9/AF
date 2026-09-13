"""
Журнал импортов событий с внешних источников.

Хранит записи о каждом запуске парсера: кто запустил, когда, сколько
событий создано/пропущено, что вывела команда.

Не удаляется мягко — это лог, его лучше хранить как есть.
Но раз у нас единый TimestampedModel — наследуемся от него тоже.
"""
from django.conf import settings
from django.db import models

from .servis_models import TimestampedModel


class ImportLog(TimestampedModel):
    """Запись о запуске парсера."""

    class Source(models.TextChoices):
        KULTISK = 'kultisk', 'kultisk.ru'
        MANUAL = 'manual', 'Вручную'
        OTHER = 'other', 'Другое'

    class Status(models.TextChoices):
        RUNNING = 'running', 'Выполняется'
        SUCCESS = 'success', 'Успешно'
        ERROR = 'error', 'Ошибка'

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.KULTISK,
        db_index=True,
        verbose_name='Источник',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RUNNING,
        db_index=True,
        verbose_name='Статус',
    )

    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Начат',
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Завершён',
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='import_logs',
        verbose_name='Кто запустил',
    )

    events_created = models.PositiveIntegerField(
        default=0,
        verbose_name='Создано событий',
    )
    events_skipped = models.PositiveIntegerField(
        default=0,
        verbose_name='Пропущено событий',
    )
    rows_parsed = models.PositiveIntegerField(
        default=0,
        verbose_name='Разобрано строк',
    )
    rows_skipped = models.PositiveIntegerField(
        default=0,
        verbose_name='Пропущено строк',
    )

    log_output = models.TextField(
        blank=True,
        verbose_name='Вывод команды',
    )

    class Meta(TimestampedModel.Meta):
        verbose_name = 'Импорт'
        verbose_name_plural = 'Импорты'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['source', 'status']),
            models.Index(fields=['-started_at']),
        ]

    def __str__(self):
        return f'{self.get_source_display()} · {self.started_at:%d.%m.%Y %H:%M}'

    @property
    def duration(self):
        """Длительность импорта в секундах. None, если ещё идёт."""
        if not self.finished_at:
            return None
        return (self.finished_at - self.started_at).total_seconds()