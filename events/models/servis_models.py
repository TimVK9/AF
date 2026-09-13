"""
Базовые абстрактные модели и переиспользуемая модель адреса.
"""

from django.db import models


class ServisModel(models.Model):
    """
    Абстрактная модель с временными метками.
    Наследуется всеми основными моделями проекта.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено',
    )

    class Meta:
        abstract = True


class Address(ServisModel):
    """
    Переиспользуемая модель адреса.

    Может быть привязана к площадке (Place) или использована отдельно.
    Координаты хранятся в DecimalField, чтобы не терять точность при
    передаче в JSON и при сортировке.
    """

    # ------------------------------------------------------------------
    # Обязательные поля
    # ------------------------------------------------------------------
    city = models.CharField(
        max_length=100,
        verbose_name='Город',
    )
    street = models.CharField(
        max_length=200,
        verbose_name='Улица',
    )
    house_number = models.CharField(
        max_length=20,
        verbose_name='Дом',
    )

    # ------------------------------------------------------------------
    # Необязательные поля
    # ------------------------------------------------------------------
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Почтовый индекс',
    )
    country = models.CharField(
        max_length=100,
        default='Россия',
        verbose_name='Страна',
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Регион/Область',
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Район',
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

    # ------------------------------------------------------------------
    # Координаты (для карт и Schema.org)
    # ------------------------------------------------------------------
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

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'
        indexes = [
            models.Index(fields=['city', 'street']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    # ==================================================================
    #  Свойства для отображения
    # ==================================================================

    @property
    def short_address(self):
        """
        Короткий адрес: 'Город, Улица, дом'.
        Используется в карточках, списках, хлебных крошках.
        """
        parts = [self.city, self.street, self.house_number]
        return ', '.join(p for p in parts if p)

    @property
    def full_address(self):
        """
        Полный адрес со всеми заполненными деталями.

        Страна выводится только если она отличается от 'Россия' —
        иначе на каждом адресе мозолило бы глаза «Россия, ...».
        """
        parts = []

        # Страна — только если не Россия
        if self.country and self.country.lower() not in ('россия', 'russia', 'ru'):
            parts.append(self.country)

        # Регион и город
        if self.region:
            parts.append(self.region)
        if self.city:
            parts.append(self.city)

        # Улица, дом, корпус
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

        # Офис / подъезд / этаж
        if self.office:
            parts.append(f"оф. {self.office}")
        if self.entrance:
            parts.append(f"подъезд {self.entrance}")
        if self.floor:
            parts.append(f"этаж {self.floor}")

        # Индекс — в конце
        if self.postal_code:
            parts.append(self.postal_code)

        return ', '.join(p for p in parts if p)

    def __str__(self):
        # short_address всегда непустой (city обязателен), поэтому безопасно
        return self.short_address or self.full_address or f"Адрес #{self.pk}"