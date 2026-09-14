"""Модель категории события."""
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from .servis_models import TimestampedModel


class Category(TimestampedModel):
    """Категория события — раздел афиши."""

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название',
    )
    slug = models.SlugField(
        unique=True,
        max_length=120,
        blank=True,
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

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Автогенерация slug с гарантией уникальности.

        Если slugify даёт пустую строку (например, имя из одних символов) —
        используем 'category'. При коллизии добавляем суффикс.
        """
        if not self.slug:
            base = slugify(self.name)[:100] or 'category'
            slug = base
            while (
                Category.all_objects
                .filter(slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base}-{get_random_string(4).lower()}"
            self.slug = slug
        super().save(*args, **kwargs)