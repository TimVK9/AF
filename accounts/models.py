"""Одноразовый код подтверждения входа."""
import hmac
import random
from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.db import models


class LegalDocument(models.Model):
    """Редакция юридического документа."""
    DOC_TYPE_CHOICES = [
        ('privacy', 'Политика конфиденциальности'),
        ('terms', 'Пользовательское соглашение (оферта)'),
    ]

    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    version = models.CharField(max_length=20, help_text='Напр. 1.0, 1.1...')
    title = models.CharField(max_length=200)
    body = models.TextField()
    effective_date = models.DateTimeField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-effective_date']
        unique_together = ['doc_type', 'version']

    def save(self, *args, **kwargs):
        if self.is_active:
            LegalDocument.objects.filter(
                doc_type=self.doc_type, is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} (v{self.version})'


class ConsentRecord(models.Model):
    """Факт согласия пользователя с конкретной редакцией документа."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consents'
    )
    document = models.ForeignKey(
        LegalDocument,
        on_delete=models.PROTECT,
        related_name='consents'
    )
    purpose = models.CharField(
        max_length=100,
        help_text='Цель: registration, newsletter, order и т.д.'
    )
    channel = models.CharField(
        max_length=100,
        default='web',
        help_text='Канал: signup-form, vk-login, profile и т.д.'
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-granted_at']
        indexes = [
            models.Index(fields=['user', 'document', 'purpose']),
        ]

    def __str__(self):
        status = 'отозвано' if self.revoked_at else 'действует'
        return f'{self.user} → {self.document} [{status}]'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Поля, которые мы хотим хранить отдельно
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    gender = models.IntegerField(null=True, blank=True, verbose_name="Пол (VK: 1-жен, 2-муж)")
    avatar_url = models.URLField(max_length=500, null=True, blank=True, verbose_name="Ссылка на аватар")

    def __str__(self):
        return f"Профиль {self.user.username}"

# Автоматически создаем профиль при создании пользователя
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class EmailOTP(models.Model):
    """Код подтверждения входа по email."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_otps',
        verbose_name='Пользователь',
    )
    code = models.CharField(max_length=6, verbose_name='Код')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    expires_at = models.DateTimeField(verbose_name='Истекает')
    is_used = models.BooleanField(default=False, verbose_name='Использован')

    class Meta:
        verbose_name = 'Email-код'
        verbose_name_plural = 'Email-коды'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
        ]

    def __str__(self):
        return f'{self.user} · {self.code}'

    @classmethod
    def issue(cls, user, lifetime_minutes=10):
        """
        Создаёт новый код, помечая все прошлые неиспользованные
        коды этого пользователя как использованные.

        Всё в транзакции, чтобы не было двух «активных» кодов.
        """
        with transaction.atomic():
            cls.objects.filter(user=user, is_used=False).update(is_used=True)
            code = f'{random.randint(0, 999999):06d}'
            return cls.objects.create(
                user=user,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=lifetime_minutes),
            )

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def matches(self, raw_code):
        """
        Проверяет, что код совпадает, не использован и не истёк.

        Сравнение через hmac.compare_digest — constant-time,
        чтобы избежать timing-атак.
        """
        if self.is_expired or self.is_used:
            return False
        return hmac.compare_digest(self.code, (raw_code or '').strip())