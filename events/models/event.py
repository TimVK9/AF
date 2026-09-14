"""Основная модель события."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from .category import Category
from .place import Place
from .servis_models import TimestampedModel


class Event(TimestampedModel):
    """Основная модель события."""

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
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

    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(
        unique=True,
        max_length=220,
        blank=True,
        verbose_name='URL',
    )
    description_short = models.CharField(max_length=500, verbose_name='Краткое описание')
    description = models.TextField(verbose_name='Полное описание')
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

    start_date = models.DateField(db_index=True, verbose_name='Дата начала')
    end_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Дата окончания',
    )
    start_time = models.TimeField(null=True, blank=True, verbose_name='Время начала')
    end_time = models.TimeField(null=True, blank=True, verbose_name='Время окончания')

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Цена',
    )
    main_image = models.ImageField(
        upload_to='events/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Главное изображение',
    )

    organizer_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Организатор',
        help_text='Название организации или имя. Необязательно.',
    )
    organizer_email = models.EmailField(blank=True, verbose_name='Email организатора')
    organizer_phone = models.CharField(max_length=30, blank=True, verbose_name='Телефон организатора')
    organizer_vk = models.URLField(
        blank=True,
        verbose_name='ВКонтакте организатора',
        help_text='Полная ссылка, например https://vk.com/club12345',
    )

    class Meta:
        ordering = ['start_date', 'start_time']
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return self.title

    # ==================================================================
    #  Свойства
    # ==================================================================
    @property
    def is_free(self):
        """Бесплатное, только если цена равна нулю."""
        return self.price is not None and self.price == 0


    @property
    def has_organizer_contacts(self):
        """Есть ли хоть один контакт организатора."""
        return any([
            self.organizer_phone,
            self.organizer_email,
            self.organizer_vk,
        ])

    @property
    def is_multi_day(self):
        """Событие длится больше одного дня."""
        return bool(self.end_date and self.end_date != self.start_date)

    # ==================================================================
    #  Валидация
    # ==================================================================
    def clean(self):
        super().clean()

        # 1. Дата окончания не раньше даты начала.
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({
                'end_date': 'Дата окончания не может быть раньше даты начала.',
            })

        # 2. Время окончания не раньше времени начала
        #    (только если это один день).
        if (
            self.start_time
            and self.end_time
            and self.start_date == self.end_date
            and self.end_time < self.start_time
        ):
            raise ValidationError({
                'end_time': 'Время окончания не может быть раньше времени начала.',
            })

        # 3. Ссылка ВК должна быть полной.
        if self.organizer_vk and not self.organizer_vk.startswith(('http://', 'https://')):
            raise ValidationError({
                'organizer_vk': 'Ссылка должна начинаться с http:// или https://',
            })

    # ==================================================================
    #  Сохранение
    # ==================================================================
    def save(self, *args, **kwargs):
        # 1. Автогенерация slug.
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


        super().save(*args, **kwargs)

    # ==================================================================
    #  Мягкое удаление с сбросом статуса
    # ==================================================================
    def delete(self, using=None, keep_parents=False):
        """
        Мягкое удаление события.

        Отличается от базового TimestampedModel.delete():
        дополнительно сбрасывает статус в DRAFT, чтобы после
        восстановления из корзины событие вернулось черновиком,
        а не опубликованным.
        """
        self.is_deleted = True
        self.status = self.Status.DRAFT
        self.save(update_fields=['is_deleted', 'status', 'updated_at'])