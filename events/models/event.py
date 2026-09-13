"""
Модель события.

Ключевое:
  • views_count убран — просмотры считаются в EventView.
  • schedule_type оставлен, но используется опционально.
  • description_short — необязательное.
  • status FINISHED ставится management-командой update_event_statuses.
  • slug генерируется в save(), при изменении title — slug не меняется.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string

from .servis_models import TimestampedModel
from .place import Place
from .category import Category


class Event(TimestampedModel):
    """Основная модель события."""

    # ==================================================================
    #  Связи
    # ==================================================================
    place = models.ForeignKey(
        Place,
        on_delete=models.PROTECT,
        related_name='events',
        verbose_name='Площадка',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        verbose_name='Категория',
    )

    # ==================================================================
    #  Choices
    # ==================================================================
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        MODERATION = 'moderation', 'На модерации'
        PUBLISHED = 'published', 'Опубликовано'
        CANCELLED = 'cancelled', 'Отменено'
        FINISHED = 'finished', 'Завершено'

    class AgeRestriction(models.TextChoices):
        ZERO = '0+', '0+'
        SIX = '6+', '6+'
        TWELVE = '12+', '12+'
        SIXTEEN = '16+', '16+'
        EIGHTEEN = '18+', '18+'

    class ScheduleType(models.TextChoices):
        SINGLE = 'single', 'Однократное'
        MULTIPLE = 'multiple', 'Многократное'
        RECURRING = 'recurring', 'Повторяющееся'

    # ==================================================================
    #  Основная информация
    # ==================================================================
    title = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    slug = models.SlugField(
        unique=True,
        max_length=220,
        blank=True,
        verbose_name='URL',
    )
    description_short = models.CharField(
        max_length=500,
        blank=True,
        default='',
        verbose_name='Краткое описание',
    )
    description = models.TextField(
        blank=True,
        default='',
        verbose_name='Полное описание',
    )
    schedule_type = models.CharField(
        max_length=20,
        choices=ScheduleType.choices,
        blank=True,
        default='',
        verbose_name='Тип расписания',
    )

    # ==================================================================
    #  Статусы и ограничения
    # ==================================================================
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        verbose_name='Статус',
    )
    age_restriction = models.CharField(
        max_length=5,
        choices=AgeRestriction.choices,
        default=AgeRestriction.SIXTEEN,
        verbose_name='Возрастное ограничение',
    )

    # ==================================================================
    #  Время проведения
    # ==================================================================
    start_date = models.DateField(
        db_index=True,
        verbose_name='Дата начала',
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Дата окончания',
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время начала',
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Время окончания',
    )

    # ==================================================================
    #  Цены
    # ==================================================================
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Цена',
    )
    is_free = models.BooleanField(
        default=False,
        verbose_name='Бесплатное',
    )

    # ==================================================================
    #  Медиа
    # ==================================================================
    main_image = models.ImageField(
        upload_to='events/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Главное изображение',
    )

    # ==================================================================
    #  Контакты
    # ==================================================================
    contact_email = models.EmailField(
        blank=True,
        verbose_name='Email для связи',
    )
    contact_phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Телефон для связи',
    )

    class Meta(TimestampedModel.Meta):
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['start_date', 'start_time']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'start_date'],
                name='uniq_event_title_start_date',
            ),
        ]

    def __str__(self):
        return self.title

    # ==================================================================
    #  Валидация
    # ==================================================================
    def clean(self):
        super().clean()

        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'Дата окончания не может быть раньше даты начала.',
            })

        same_day = (
            self.end_date is None
            or self.end_date == self.start_date
        )
        if (
            same_day
            and self.start_time
            and self.end_time
            and self.end_time < self.start_time
        ):
            raise ValidationError({
                'end_time': 'Время окончания не может быть раньше времени начала.',
            })

        if self.end_time and not self.start_time:
            raise ValidationError({
                'end_time': 'Укажите время начала, прежде чем задавать время окончания.',
            })

        if self.is_free and self.price:
            raise ValidationError({
                'price': 'У бесплатного события не может быть цены.',
            })

    # ==================================================================
    #  Сохранение
    # ==================================================================
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or 'event'
            slug = base
            while (
                Event.all_objects
                .filter(slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base}-{get_random_string(4).lower()}"
            self.slug = slug

        if self.is_free:
            self.price = None

        super().save(*args, **kwargs)

    # ==================================================================
    #  Дополнительные свойства
    # ==================================================================

    @property
    def is_multiday(self):
        return (
            self.end_date
            and self.end_date != self.start_date
        )

    @property
    def is_cancelled(self):
        return self.status == self.Status.CANCELLED

    @property
    def is_past(self):
        from django.utils import timezone
        today = timezone.localdate()
        end = self.end_date or self.start_date
        return end < today

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('events:event_detail', kwargs={'slug': self.slug})