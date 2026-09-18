"""Модель площадки проведения события."""
from django.db import models
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from .servis_models import TimestampedModel


MONTH_CHOICES = [
    (1, 'Январь'), (2, 'Февраль'), (3, 'Март'), (4, 'Апрель'),
    (5, 'Май'), (6, 'Июнь'), (7, 'Июль'), (8, 'Август'),
    (9, 'Сентябрь'), (10, 'Октябрь'), (11, 'Ноябрь'), (12, 'Декабрь'),
]


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



    latitude = models.FloatField(
        null=True, blank=True,
        verbose_name='Широта',
        help_text='Например: 54.6333',
    )
    longitude = models.FloatField(
        null=True, blank=True,
        verbose_name='Долгота',
        help_text='Например: 83.3000',
    )

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
    def lat_str(self):
        """Координата с точкой, независимо от локали."""
        return f"{self.latitude:.6f}" if self.latitude else ""

    @property
    def lng_str(self):
        """Координата с точкой, независимо от локали."""
        return f"{self.longitude:.6f}" if self.longitude else ""

        
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

    def is_open_on(self, d):
        """Возвращает True, если площадка работает в указанную дату.

        Если сезоны не заданы — считается, что открыто каждый день.
        """
        seasons = self.working_seasons.all()
        if not seasons.exists():
            return True

        weekday = d.weekday()  # 0=пн, 6=вс
        mmdd = f'{d.month:02d}-{d.day:02d}'

        for season in seasons:
            s = f'{season.start_month:02d}-{season.start_day:02d}'
            e = f'{season.end_month:02d}-{season.end_day:02d}'

            # Сезон может переходить через год (сентябрь → май)
            if s <= e:
                in_season = s <= mmdd <= e
            else:
                in_season = mmdd >= s or mmdd <= e

            if in_season:
                return season.is_open_on_weekday(weekday)

        # Если дата не попала ни в один сезон — считаем открытым
        return True

    def working_hours_display(self):
        """Возвращает список словарей: [{'name': 'Летний период', 'time': 'Пн-Вс 10:00—17:00'}]."""
        seasons = self.working_seasons.all().order_by('order')
        if not seasons:
            return []

        WEEKDAYS_SHORT = {
            0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт',
            4: 'Пт', 5: 'Сб', 6: 'Вс',
        }
        ALL_DAYS = list(range(7))

        result = []
        for season in seasons:
            open_days = [d for d in ALL_DAYS if season.is_open_on_weekday(d)]

            # Группируем подряд идущие дни
            groups = []
            current_group = [open_days[0]]
            for d in open_days[1:]:
                if d == current_group[-1] + 1:
                    current_group.append(d)
                else:
                    groups.append(current_group)
                    current_group = [d]
            groups.append(current_group)

            day_labels = []
            for g in groups:
                if len(g) == 1:
                    day_labels.append(WEEKDAYS_SHORT[g[0]])
                else:
                    day_labels.append(
                        f'{WEEKDAYS_SHORT[g[0]]}-{WEEKDAYS_SHORT[g[-1]]}'
                    )

            schedule_line = ', '.join(day_labels)
            if season.time:
                schedule_line += f'  {season.time}'

            result.append({
                'name': season.name,
                'time': schedule_line,
            })

        return result



class WorkingSeason(TimestampedModel):
    """Сезон работы площадки (например, летний и зимний)."""

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='working_seasons',
        verbose_name='Площадка',
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Название периода',
        help_text='Например: «Летний период» или «Зимний период»',
    )
    start_month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES,
        verbose_name='Месяц начала',
    )
    start_day = models.PositiveSmallIntegerField(
        verbose_name='День начала',
        help_text='Число от 1 до 31',
    )
    end_month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES,
        verbose_name='Месяц окончания',
    )
    end_day = models.PositiveSmallIntegerField(
        verbose_name='День окончания',
        help_text='Число от 1 до 31',
    )

    open_mon = models.BooleanField(default=True, verbose_name='Понедельник')
    open_tue = models.BooleanField(default=True, verbose_name='Вторник')
    open_wed = models.BooleanField(default=True, verbose_name='Среда')
    open_thu = models.BooleanField(default=True, verbose_name='Четверг')
    open_fri = models.BooleanField(default=True, verbose_name='Пятница')
    open_sat = models.BooleanField(default=True, verbose_name='Суббота')
    open_sun = models.BooleanField(default=True, verbose_name='Воскресенье')

    time = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Часы работы',
        help_text='Например: «10:00 — 17:00, пт до 16:00»',
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='Порядок сортировки',
    )

    class Meta:
        verbose_name = 'Сезон работы'
        verbose_name_plural = 'Сезоны работы'
        ordering = ['order', 'id']
        indexes = [
            models.Index(fields=['place', 'order']),
        ]

    def __str__(self):
        return f'{self.name} — {self.place.name}'

    def is_open_on_weekday(self, weekday):
        """weekday: 0=понедельник, 6=воскресенье."""
        flags = [
            self.open_mon, self.open_tue, self.open_wed, self.open_thu,
            self.open_fri, self.open_sat, self.open_sun,
        ]
        return flags[weekday]
