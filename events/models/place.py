"""
Модель площадки проведения события.

Адрес теперь внутри Place — отдельная модель Address убрана.
Площадка без адреса невозможна, поэтому нет смысла в отдельной таблице.

Поля адреса:
  city, street, house_number, building, office, entrance, floor,
  landmark, postal_code, latitude, longitude
"""
from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string

from .servis_models import TimestampedModel


class Place(TimestampedModel):
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

    # ==================================================================
    #  Контакты
    # ==================================================================
    website = models.URLField(
        blank=True,
        verbose_name='Сайт',
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Телефон',
    )
    vk_url = models.URLField(
        blank=True,
        verbose_name='ВКонтакте',
        help_text='Полная ссылка на страницу, например https://vk.com/club12345',
    )
    email = models.EmailField(
        blank=True,
        verbose_name='Email',
    )

    # ==================================================================
    #  Адрес — прямо здесь, без отдельной модели
    # ==================================================================
    city = models.CharField(
        max_length=100,
        default='Искитим',
        verbose_name='Город',
    )
    street = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Улица',
    )
    house_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Дом',
    )
    building = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Корпус/Строение',
    )
    office = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Офис/Квартира',
    )
    entrance = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Вход/Подъезд',
    )
    floor = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Этаж',
    )
    landmark = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Ориентир',
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Почтовый индекс',
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Широта',
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name='Долгота',
    )

    # ==================================================================
    #  Медиа
    # ==================================================================
    main_image = models.ImageField(
        upload_to='places/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Главное фото',
    )

    class Meta(TimestampedModel.Meta):
        verbose_name = 'Площадка'
        verbose_name_plural = 'Площадки'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['city', 'street']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return self.name

    # ==================================================================
    #  Автогенерация slug
    # ==================================================================
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:250] or 'place'
            slug = base
            while (
                Place.all_objects
                .filter(slug=slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                slug = f"{base}-{get_random_string(4).lower()}"
            self.slug = slug
        super().save(*args, **kwargs)

    # ==================================================================
    #  Свойства для отображения
    # ==================================================================

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
        if self.building:
            street_line = f"{street_line}, корп. {self.building}"
        if street_line:
            parts.append(street_line)

        if self.office:
            parts.append(f"оф. {self.office}")
        if self.entrance:
            parts.append(f"подъезд {self.entrance}")
        if self.floor:
            parts.append(f"этаж {self.floor}")
        if self.postal_code:
            parts.append(self.postal_code)

        return ', '.join(p for p in parts if p)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('events:place_detail', kwargs={'slug': self.slug})