"""
Модели аналитики — разделены по типам.

Каждая модель хранит дневные счётчики и связана с объектом через
настоящий ForeignKey с on_delete=CASCADE. Удалили событие — снеслись
и его счётчики.

Принцип: НЕ сохраняем ПДн. Только агрегаты «сколько раз за день
посмотрели объект X». Никаких IP, User-Agent, cookies.
"""
from django.db import models


class AbstractDailyView(models.Model):
    """
    Абстрактная база: (объект, дата) — уникальная пара, count — счётчик.
    Наследники добавляют свой FK на конкретную модель.
    """
    date = models.DateField(
        db_index=True,
        verbose_name='Дата',
    )
    count = models.PositiveIntegerField(
        default=0,
        verbose_name='Просмотров',
    )

    class Meta:
        abstract = True
        ordering = ['-date']


class EventView(AbstractDailyView):
    """Просмотры события по дням."""
    event = models.ForeignKey(
        'Event',
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='Событие',
    )

    class Meta(AbstractDailyView.Meta):
        verbose_name = 'Просмотр события'
        verbose_name_plural = 'Просмотры событий'
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'date'],
                name='uniq_eventview_event_date',
            ),
        ]

    def __str__(self):
        return f'{self.event_id} · {self.date:%d.%m.%Y} · {self.count}'


class PlaceView(AbstractDailyView):
    """Просмотры площадки по дням."""
    place = models.ForeignKey(
        'Place',
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='Площадка',
    )

    class Meta(AbstractDailyView.Meta):
        verbose_name = 'Просмотр площадки'
        verbose_name_plural = 'Просмотры площадок'
        constraints = [
            models.UniqueConstraint(
                fields=['place', 'date'],
                name='uniq_placeview_place_date',
            ),
        ]

    def __str__(self):
        return f'{self.place_id} · {self.date:%d.%m.%Y} · {self.count}'


class CategoryView(AbstractDailyView):
    """Просмотры категории по дням."""
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='Категория',
    )

    class Meta(AbstractDailyView.Meta):
        verbose_name = 'Просмотр категории'
        verbose_name_plural = 'Просмотры категорий'
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'date'],
                name='uniq_categoryview_category_date',
            ),
        ]

    def __str__(self):
        return f'{self.category_id} · {self.date:%d.%m.%Y} · {self.count}'


class SiteView(AbstractDailyView):
    """
    Просмотры «служебных» страниц: главная, поиск.
    Не привязаны к конкретному объекту.
    """

    class Kind(models.TextChoices):
        HOME = 'home', 'Главная'
        SEARCH = 'search', 'Поиск'

    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        db_index=True,
        verbose_name='Страница',
    )

    class Meta(AbstractDailyView.Meta):
        verbose_name = 'Просмотр страницы'
        verbose_name_plural = 'Просмотры страниц'
        constraints = [
            models.UniqueConstraint(
                fields=['kind', 'date'],
                name='uniq_siteview_kind_date',
            ),
        ]

    def __str__(self):
        return f'{self.get_kind_display()} · {self.date:%d.%m.%Y} · {self.count}'