"""
Модель категории события.
"""

from django.db import models

from .servis_models import ServisModel


class Category(ServisModel):
    """Категория события."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название',
    )
    slug = models.SlugField(
        unique=True,
        max_length=120,
        verbose_name='URL',
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Иконка',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активна',
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок',
    )

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']
        # Index(fields=['slug']) не нужен: unique=True создаёт индекс сам.

    def __str__(self):
        return self.name