"""
Модель площадки проведения события.
"""

from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string

from .servis_models import ServisModel, Address


class Place(ServisModel):
    """Площадка проведения события."""

    name = models.CharField(
        max_length=255,
        verbose_name='Название',
    )
    slug = models.SlugField(
        unique=True,
        max_length=270,
        blank=True,
        verbose_name='URL',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание',
    )
    website = models.URLField(
        blank=True,
        verbose_name='Сайт',
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Телефон',
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email',
    )

    # ForeignKey, а не OneToOne: в одном здании может быть несколько площадок
    # (например, два зала в одном ТЦ).
    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='places',
        verbose_name='Адрес',
    )

    main_image = models.ImageField(
        upload_to='places/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Главное фото',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Площадка'
        verbose_name_plural = 'Площадки'
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    # ==================================================================
    #  Автогенерация slug с защитой от коллизий
    # ==================================================================
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:250] or 'place'
            slug = base
            # Если slug занят другим объектом — добавляем случайный суффикс
            while (
                Place.objects
                .filter(slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base}-{get_random_string(4).lower()}"
            self.slug = slug
        super().save(*args, **kwargs)