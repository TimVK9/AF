"""
Модель обезличенной статистики просмотров.

ВАЖНО: мы НЕ сохраняем персональные данные.
Только агрегированные счётчики: «сколько раз за день посмотрели событие X».

Никаких IP, User-Agent, cookies, session_id, идентификаторов пользователя.
"""

from django.db import models


class PageView(models.Model):
    """Счётчик просмотров по дням. Обезличенный."""

    class Kind(models.TextChoices):
        EVENT = "event", "Событие"
        PLACE = "place", "Площадка"
        CATEGORY = "category", "Категория"
        HOME = "home", "Главная"
        SEARCH = "search", "Поиск"

    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        db_index=True,
        verbose_name="Тип",
    )

    # object_id = 0 означает «не применимо» (для главной и поиска).
    # Используем 0 вместо NULL, потому что в SQL NULL != NULL, и
    # unique_together с NULL не работал бы — можно было бы создать
    # сколько угодно дублирующих записей за один день.
    object_id = models.PositiveIntegerField(
        default=0,
        db_index=True,
        verbose_name="ID объекта",
    )

    date = models.DateField(
        db_index=True,
        verbose_name="Дата",
    )
    count = models.PositiveIntegerField(
        default=0,
        verbose_name="Просмотров",
    )

    class Meta:
        verbose_name = "Просмотр"
        verbose_name_plural = "Просмотры"
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "object_id", "date"],
                name="unique_pageview_kind_object_date",
            ),
        ]
        indexes = [
            models.Index(fields=["kind", "date"]),
            models.Index(fields=["object_id", "date"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        """Человекочитаемое представление: название объекта + дата + просмотры."""
        return f"{self.get_object_name()} · {self.date:%d.%m.%Y} · {self.count} просм."

    def get_object_name(self):
        """
        Возвращает название объекта в зависимости от kind.
        Импорты внутри метода — чтобы избежать циклических зависимостей.
        """
        if self.kind == self.Kind.EVENT and self.object_id:
            from .event import Event
            try:
                return Event.objects.get(pk=self.object_id).title
            except Event.DoesNotExist:
                return f"Событие #{self.object_id} (удалено)"

        if self.kind == self.Kind.PLACE and self.object_id:
            from .place import Place
            try:
                return Place.objects.get(pk=self.object_id).name
            except Place.DoesNotExist:
                return f"Площадка #{self.object_id} (удалена)"

        if self.kind == self.Kind.CATEGORY and self.object_id:
            from .category import Category
            try:
                return Category.objects.get(pk=self.object_id).name
            except Category.DoesNotExist:
                return f"Категория #{self.object_id} (удалена)"

        if self.kind == self.Kind.HOME:
            return "Главная страница"

        if self.kind == self.Kind.SEARCH:
            return "Поиск"

        return self.get_kind_display()