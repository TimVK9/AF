"""
Базовые абстрактные модели.

TimestampedModel — общий предок всех моделей проекта:
  • created_at / updated_at;
  • is_deleted — для мягкого удаления;
  • objects — менеджер, который НЕ показывает удалённые;
  • all_objects — менеджер, который показывает всё.

Soft delete реализован через переопределение delete().
"""
from django.db import models


class ActiveManager(models.Manager):
    """Менеджер по умолчанию — скрывает удалённые объекты."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class TimestampedModel(models.Model):
    """
    Абстрактная модель с временными метками и мягким удалением.

    Использование:
        Model.objects.all()       # только неудалённые
        Model.all_objects.all()   # все, включая удалённые
        obj.delete()              # мягкое удаление (is_deleted=True)
        obj.hard_delete()         # настоящее удаление из БД
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Создано',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Обновлено',
    )
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Удалено',
    )

    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def delete(self, using=None, keep_parents=False):
        """Мягкое удаление: помечает is_deleted=True."""
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Настоящее удаление из БД. Использовать осторожно."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Восстановление после мягкого удаления."""
        self.is_deleted = False
        self.save(update_fields=['is_deleted', 'updated_at'])