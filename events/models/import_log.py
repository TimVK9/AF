"""
Журнал импортов событий из внешних источников.

Хранит: когда запускали, кто запускал, что вышло.
"""

from django.conf import settings
from django.db import models


class ImportLog(models.Model):
    """Одна запись = один запуск парсера."""

    class Source(models.TextChoices):
        KULTISK = 'kultisk', 'kultisk.ru'

    class Status(models.TextChoices):
        RUNNING = 'running', 'Выполняется'
        SUCCESS = 'success', 'Успешно'
        ERROR = 'error', 'Ошибка'

    source = models.CharField(
        max_length=50,
        choices=Source.choices,
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
        verbose_name='Запущен',
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
        verbose_name='Пропущено (дубли)',
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
        verbose_name='Вывод',
    )

    class Meta:
        verbose_name = 'Импорт'
        verbose_name_plural = 'Импорты'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.get_source_display()} · {self.started_at:%d.%m.%Y %H:%M}'