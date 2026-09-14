"""
Базовые абстрактные модели и менеджеры.

- SoftDeleteQuerySet — QuerySet с методами массового удаления.
- SoftDeleteManager — менеджер по умолчанию, скрывает удалённые.
- AllObjectsManager — показывает всё, включая удалённые.
- TimestampedModel — абстрактная база: created_at / updated_at / is_deleted.
"""
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet с методами мягкого удаления и восстановления."""

    def delete(self):
        """Массовое мягкое удаление: проставляет is_deleted=True."""
        return self.update(is_deleted=True, updated_at=timezone.now())

    def hard_delete(self):
        """Настоящее удаление из БД. Осторожно."""
        return super().delete()

    def alive(self):
        """Только неудалённые записи."""
        return self.filter(is_deleted=False)

    def dead(self):
        """Только удалённые записи."""
        return self.filter(is_deleted=True)

    def restore(self):
        """Массовое восстановление."""
        return self.update(is_deleted=False, updated_at=timezone.now())


class SoftDeleteManager(models.Manager):
    """
    Менеджер по умолчанию. Скрывает записи с is_deleted=True.
    Именно его Django использует как `Model.objects`.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """
    Показывает все записи, включая удалённые.
    Доступен как `Model.all_objects`.
    """

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class TimestampedModel(models.Model):
    """
    Абстрактная база.

    Содержит:
    - created_at, updated_at — временные метки;
    - is_deleted — флаг мягкого удаления;
    - objects — менеджер, скрывающий удалённые;
    - all_objects — менеджер, показывающий всё.
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Удалено',
    )

    # ВАЖНО: objects идёт первым — он становится менеджером по умолчанию.
    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True
        # ordering не задаём: каждая модель определяет свой порядок.
        # Иначе '-created_at' унаследуется во все модели и будет мешать.

    def delete(self, using=None, keep_parents=False):
        """Мягкое удаление: помечает is_deleted=True."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Настоящее удаление из БД."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Восстановление после мягкого удаления."""
        self.is_deleted = False
        self.save(update_fields=['is_deleted', 'updated_at'])