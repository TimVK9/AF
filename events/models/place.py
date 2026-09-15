"""Модель площадки проведения события."""
from django.db import models
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from .servis_models import TimestampedModel


class Place(TimestampedModel):
    """Площадка: театр, клуб, стадион, ДК и т.п."""

    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(
        unique=True,
        max_length=270,
        blank=True,
        verbose_name='URL',
    )
    description = models.TextField(blank=True, verbose_name='Описание')
    website = models.URLField(blank=True, verbose_name='Сайт')
    phone = models.CharField(max_length=30, blank=True, verbose_name='Телефон')
    vk_url = models.URLField(
        blank=True,
        verbose_name='ВКонтакте',
        help_text='Полная ссылка, например https://vk.com/club12345',
    )
    email = models.EmailField(blank=True, verbose_name='Email')

    city = models.CharField(max_length=100, default='Искитим', verbose_name='Город')
    street = models.CharField(max_length=200, blank=True, verbose_name='Улица')
    house_number = models.CharField(max_length=20, blank=True, verbose_name='Дом')
    building = models.CharField(max_length=20, blank=True, verbose_name='Корпус/Строение')
    office = models.CharField(max_length=20, blank=True, verbose_name='Офис/Квартира')
    floor = models.CharField(max_length=20, blank=True, verbose_name='Этаж')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='Почтовый индекс')

    main_image = models.ImageField(
        upload_to='places/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Главное фото',
    )

    class Meta:
        verbose_name = 'Площадка'
        verbose_name_plural = 'Площадки'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['city', 'street']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Автогенерация уникального slug."""
        if not self.slug:
            base = slugify(self.name, allow_unicode=True)[:250] or 'place'
            slug = base
            while (
                Place.objects
                .filter(slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base}-{get_random_string(4).lower()}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def short_address(self):
        """Короткий адрес: 'Город, Улица, дом'."""
        parts = [self.city, self.street, self.house_number]
        return ', '.join(p for p in parts if p)

    @property
    def full_address(self):
        """Полный адрес со всеми заполненными деталями."""
        parts = []
        if self.city:
            parts.append(self.city)

        street_line = self.street
        if self.house_number:
            street_line = (
                f"{street_line}, д. {self.house_number}"
                if street_line
                else f"д. {self.house_number}"
            )
        if street_line:
            parts.append(street_line)

        if self.building:
            parts.append(f"корп. {self.building}")
        if self.office:
            parts.append(f"оф. {self.office}")
        if self.floor:
            parts.append(f"этаж {self.floor}")

        return ', '.join(parts)

    def get_absolute_url(self):
        return reverse('events:place_detail', kwargs={'slug': self.slug})