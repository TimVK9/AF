"""
Модель категории события.
"""
from django.db import models
from django.utils.text import slugify

from .servis_models import TimestampedModel


class Category(TimestampedModel):
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

    class Meta(TimestampedModel.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:120] or 'category'
        super().save(*args, **kwargs)