from django.db import models


class InterestResponse(models.Model):
    email = models.EmailField(
        unique=True,
        verbose_name='Email',
    )
    comment = models.TextField(
        blank=True,
        verbose_name='Комментарий (опционально)',
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='IP адрес',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )

    class Meta:
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} — {self.created_at.strftime('%d.%m.%Y %H:%M')}"
