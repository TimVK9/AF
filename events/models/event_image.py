"""
Дополнительные изображения события (галерея).

У каждого события может быть несколько фотографий.
Первое по order — основное в галерее.
"""
from django.db import models

from .servis_models import ServisModel


class EventImage(ServisModel):
    """Изображение в галерее события."""

    event = models.ForeignKey(
        "Event",
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Событие",
    )
    image = models.ImageField(
        upload_to="events/gallery/%Y/%m/",
        verbose_name="Изображение",
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Подпись",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )

    class Meta:
        verbose_name = "Изображение галереи"
        verbose_name_plural = "Изображения галереи"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.event.title} — фото #{self.pk}"