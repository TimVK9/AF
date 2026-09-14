"""
Глобальные настройки сайта — редактируются через админку.
Всегда одна запись (singleton, pk=1).
"""
from django.db import models


class SiteSettings(models.Model):
    """
    Глобальные настройки сайта.

    Используется через SiteSettings.load() — вернёт единственный
    объект, создаст при первом обращении.
    """

    coming_soon = models.BooleanField(
        default=False,
        verbose_name='Режим «Скоро запуск»',
        help_text='Если включено — все не-админы видят заглушку.',
    )
    coming_soon_message = models.TextField(
        blank=True,
        verbose_name='Сообщение на заглушке',
        help_text='Необязательно. Показывается на странице «Скоро запуск».',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено',
    )

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def __str__(self):
        return 'Настройки сайта'

    def save(self, *args, **kwargs):
        """Синглтон: всегда pk=1."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Запрещаем удалять единственную запись."""
        pass

    @classmethod
    def load(cls):
        """Возвращает единственный объект настроек, создаёт при отсутствии."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj