from django.db import models
from .servis_models import ServisModel, Address
from django.utils.text import slugify


class Place(ServisModel):
    """Площадка проведения события"""

    name = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(unique=True, max_length=270, verbose_name='URL')
    description = models.TextField(blank=True, verbose_name='Описание')
    website = models.URLField(blank=True, verbose_name='Сайт')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True, related_name='place', verbose_name='Адрес')
    main_image = models.ImageField(upload_to='places/%Y/%m/', null=True, blank=True, verbose_name='Главное фото')


    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    



