"""Базовая абстрактная модель."""
from django.db import models


class TimestampedModel(models.Model):
    """Абстрактная базовая модель: метки времени + статус."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        MODERATION = 'moderation', 'На модерации'
        PUBLISHED = 'published', 'Опубликовано'

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name='Статус',
    )

    class Meta:
        abstract = True