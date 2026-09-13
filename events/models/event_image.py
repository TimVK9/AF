"""
Дополнительные изображения события (галерея).
"""
from django.db import models

from .servis_models import TimestampedModel


class EventImage(TimestampedModel):
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

    class Meta(TimestampedModel.Meta):
        verbose_name = "Изображение галереи"
        verbose_name_plural = "Изображения галереи"
        ordering = ["order", "id"]
        indexes = [
            models.Index(fields=["event", "order"]),
        ]

    def __str__(self):
        return f"Фото #{self.pk} (событие #{self.event_id})"

    def save(self, *args, **kwargs):
        """Автопорядок: если order=0 — ставим в конец."""
        if not self.order and self.event_id:
            last = (
                EventImage.all_objects
                .filter(event_id=self.event_id)
                .exclude(pk=self.pk)
                .order_by('-order')
                .first()
            )
            self.order = (last.order + 1) if last else 1
        super().save(*args, **kwargs)