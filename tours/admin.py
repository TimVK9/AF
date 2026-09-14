from django.contrib import admin

# Register your models here.
"""Админка для гастрольных событий."""
from django.contrib import admin

from .models import TourEvent, TourVenue


@admin.register(TourVenue)
class TourVenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'kassir_slug', 'events_count')
    search_fields = ('name', 'city', 'kassir_slug')
    ordering = ('name',)

    @admin.display(description='Событий')
    def events_count(self, obj):
        return obj.events.count()


@admin.register(TourEvent)
class TourEventAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'venue', 'category', 'start_date',
        'price_display_short', 'is_published', 'is_active',
    )
    list_filter = ('category', 'is_published', 'is_active', 'venue__city')
    search_fields = ('title', 'external_id', 'kassir_url')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    list_editable = ('is_published', 'is_active')
    list_per_page = 30

    fieldsets = (
        ('Основное', {
            'fields': ('title', 'slug', 'external_id', 'kassir_url', 'category'),
        }),
        ('Дата и время', {
            'fields': ('start_date', 'end_date', 'start_time'),
        }),
        ('Площадка', {
            'fields': ('venue',),
        }),
        ('Цена', {
            'fields': ('price_min', 'price_max', 'price_text'),
        }),
        ('Дополнительно', {
            'fields': ('age_restriction', 'image_url', 'description'),
        }),
        ('Управление', {
            'fields': ('is_published', 'is_active'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Цена')
    def price_display_short(self, obj):
        if obj.price_min is None:
            return '—'
        if obj.price_min == 0:
            return 'Бесплатно'
        return f'{obj.price_min} ₽'
