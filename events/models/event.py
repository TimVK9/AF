from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError
from .servis_models import ServisModel
from .place import Place
from .category import Category
from django.contrib.auth import get_user_model

User = get_user_model()

class Event(ServisModel):
    """Основная модель события"""

    # Связи
    place = models.ForeignKey(Place, on_delete=models.PROTECT, related_name='events', verbose_name='Площадка')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='events', verbose_name='Категория')

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
    # Основная информация
    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, max_length=220, verbose_name='URL')
    description_short = models.CharField(max_length=500, verbose_name='Краткое описание')
    description = models.TextField(verbose_name='Полное описание')
    schedule_type = models.CharField(
    max_length=20,
    choices=ScheduleType.choices,
    null=True,  # ← разрешить NULL
    blank=True,  # ← разрешить пустое в формах
    verbose_name='Тип расписания'
)
    # Статусы и ограничения
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True, verbose_name='Статус')
    age_restriction = models.CharField(max_length=5, choices=AgeRestriction.choices, default=AgeRestriction.SIXTEEN, verbose_name='Возрастное ограничение')

    # Время проведения
    start_date = models.DateField(db_index=True, verbose_name='Дата начала')
    end_date = models.DateField(null=True, blank=True, verbose_name='Дата окончания')
    start_time = models.TimeField(null=True, blank=True, verbose_name='Время начала')

    # Цены
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Цена')
    is_free = models.BooleanField(default=False, verbose_name='Бесплатное')

    # Медиа
    main_image = models.ImageField(upload_to='events/%Y/%m/', null=True, blank=True, verbose_name='Главное изображение')
   
    # Контакты для связи
    contact_email = models.EmailField(blank=True, verbose_name='Email для связи')
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон для связи')

    # Счётчики
    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    favorites_count = models.PositiveIntegerField(default=0, verbose_name='В избранном')

    class Meta:
        ordering = ['start_date', 'start_time']
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        

    def __str__(self):
        return self.title




