"""Модели для гастрольных событий, импортированных с kassir.ru."""
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class TourVenue(models.Model):
    """Площадка, на которой проходят гастрольные события."""

    name = models.CharField(max_length=255, verbose_name='Название')
    city = models.CharField(max_length=100, default='Новосибирск', verbose_name='Город')
    address = models.CharField(max_length=500, blank=True, verbose_name='Адрес')
    kassir_slug = models.CharField(
        max_length=255, unique=True, blank=True, null=True,
        verbose_name='Slug на kassir.ru',
        help_text='Например: novosibirskiy-gosudarstvennyy-akademicheskiy-tetar-operyi-i-baleta',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Площадка гастролей'
        verbose_name_plural = 'Площадки гастролей'

    def __str__(self):
        return f'{self.name} ({self.city})'


class TourEvent(models.Model):
    """Гастрольное событие, импортированное с kassir.ru."""

    class Category(models.TextChoices):
        THEATRE = 'theatre', 'Театр'
        CONCERT = 'concert', 'Концерт'
        SHOW = 'show', 'Шоу'
        OTHER = 'other', 'Другое'

    class AgeRestriction(models.TextChoices):
        ZERO = '0+', '0+'
        SIX = '6+', '6+'
        TWELVE = '12+', '12+'
        SIXTEEN = '16+', '16+'
        EIGHTEEN = '18+', '18+'

    external_id = models.CharField(
        max_length=100, unique=True, db_index=True,
        verbose_name='ID на kassir.ru',
    )
    title = models.CharField(max_length=300, verbose_name='Название')
    slug = models.SlugField(max_length=320, unique=True, verbose_name='URL')
    description = models.TextField(blank=True, default='', verbose_name='Описание')
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.THEATRE,
        verbose_name='Категория',
    )
    venue = models.ForeignKey(
        TourVenue,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Площадка',
    )

    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания')
    start_time = models.TimeField(null=True, blank=True, verbose_name='Время начала')

    price_min = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Минимальная цена',
    )
    price_max = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        verbose_name='Максимальная цена',
    )
    price_text = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Цена (текстом)',
        help_text='Как на kassir.ru, например «от 3 000 ₽»',
    )

    age_restriction = models.CharField(
        max_length=5,
        choices=AgeRestriction.choices,
        default=AgeRestriction.SIXTEEN,
        verbose_name='Возрастное ограничение',
    )

    image_url = models.URLField(blank=True, default='', verbose_name='URL изображения')
    kassir_url = models.URLField(verbose_name='Ссылка на kassir.ru')

    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    is_active = models.BooleanField(
        default=True, db_index=True,
        verbose_name='Актуально',
        help_text='Снимается, если событие пропало с kassir.ru',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    last_parsed_at = models.DateTimeField(null=True, blank=True, verbose_name='Последний парсинг')

    class Meta:
        ordering = ['start_date', 'start_time']
        verbose_name = 'Гастрольное событие'
        verbose_name_plural = 'Гастрольные события'
        indexes = [
            models.Index(fields=['is_published', 'is_active', 'start_date']),
            models.Index(fields=['category', 'start_date']),
        ]

    def __str__(self):
        return self.title

    @property
    def is_free(self):
        return self.price_min is not None and self.price_min == 0

    @property
    def price_display(self):
        if self.price_min is None:
            return 'Уточняется'
        if self.price_min == 0:
            return 'Бесплатно'
        if self.price_max and self.price_max != self.price_min:
            return f'{self.price_min} — {self.price_max} ₽'
        return f'{self.price_min} ₽'

# Create your models here.
