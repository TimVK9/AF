"""
Админка приложения events.

Показывает:
  • Event — список с фильтрами по статусу, категории, площадке;
  • Place — площадки;
  • Address — адреса;
  • Category — категории;
  • EventImage — изображения галереи (инлайн в Event).

Без кастомных format_html на list_display — Django 5+/6 требует
аргументы, а где они не нужны, проще mark_safe или обычный текст.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    Event,
    EventImage,
    Place,
    Address,
    Category,
)


# ======================================================================
#  EVENT IMAGE (inline)
# ======================================================================

class EventImageInline(admin.TabularInline):
    """Галерея изображений — прямо в карточке события."""
    model = EventImage
    extra = 1
    fields = ('image', 'caption', 'order', 'preview')
    readonly_fields = ('preview',)
    ordering = ('order', 'id')

    @admin.display(description='Превью')
    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 80px; border-radius: 4px;">',
                obj.image.url,
            )
        return '—'


# ======================================================================
#  EVENT
# ======================================================================

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'place',
        'start_date',
        'end_date',
        'status',
        'is_free',
        'price',
        'views_count',
    )
    list_filter = (
        'status',
        'is_free',
        'category',
        'place',
        'age_restriction',
        'start_date',
    )
    search_fields = (
        'title',
        'description_short',
        'description',
        'place__name',
    )
    date_hierarchy = 'start_date'
    ordering = ('-start_date', '-start_time')
    list_per_page = 30
    list_select_related = ('category', 'place')

    inlines = [EventImageInline]

    readonly_fields = ('views_count', 'favorites_count', 'created_at', 'updated_at')

    fieldsets = (
        ('Основное', {
            'fields': (
                'title',
                'slug',
                'category',
                'place',
                'description_short',
                'description',
                'schedule_type',
            ),
        }),
        ('Статус и ограничения', {
            'fields': (
                'status',
                'age_restriction',
            ),
        }),
        ('Дата и время', {
            'fields': (
                ('start_date', 'end_date'),
                ('start_time', 'end_time'),
            ),
        }),
        ('Стоимость', {
            'fields': ('is_free', 'price'),
        }),
        ('Медиа', {
            'fields': ('main_image',),
        }),
        ('Контакты', {
            'fields': ('contact_email', 'contact_phone'),
        }),
        ('Счётчики и служебное', {
            'classes': ('collapse',),
            'fields': (
                ('views_count', 'favorites_count'),
                ('created_at', 'updated_at'),
            ),
        }),
    )

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('title',)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'place')


# ======================================================================
#  PLACE
# ======================================================================

@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'city',
        'address_short',
        'phone',
        'email',
    )
    search_fields = (
        'name',
        'description',
        'phone',
        'email',
        'address__city',
        'address__street',
    )
    ordering = ('name',)
    list_per_page = 30
    list_select_related = ('address',)
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Основное', {
            'fields': (
                'name',
                'slug',
                'description',
            ),
        }),
        ('Адрес', {
            'fields': ('address',),
        }),
        ('Контакты', {
            'fields': ('website', 'phone', 'email'),
        }),
        ('Медиа', {
            'fields': ('main_image',),
        }),
    )

    @admin.display(description='Город', ordering='address__city')
    def city(self, obj):
        return obj.address.city if obj.address else '—'

    @admin.display(description='Адрес')
    def address_short(self, obj):
        if obj.address:
            return obj.address.short_address
        return '—'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('address')


# ======================================================================
#  ADDRESS
# ======================================================================

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        'short_address_display',
        'city',
        'region',
        'postal_code',
        'country',
    )
    list_filter = ('country', 'region', 'city')
    search_fields = (
        'city',
        'street',
        'house_number',
        'postal_code',
        'region',
    )
    ordering = ('city', 'street', 'house_number')
    list_per_page = 30

    fieldsets = (
        ('Обязательное', {
            'fields': (
                ('city', 'street', 'house_number'),
            ),
        }),
        ('Дополнительное', {
            'fields': (
                ('postal_code', 'country', 'region'),
                ('district', 'building', 'office'),
                ('entrance', 'floor', 'landmark'),
            ),
        }),
        ('Координаты', {
            'fields': (
                ('latitude', 'longitude'),
            ),
        }),
    )

    @admin.display(description='Адрес')
    def short_address_display(self, obj):
        return obj.short_address or '—'


# ======================================================================
#  CATEGORY
# ======================================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'icon',
        'is_active',
        'order',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'description')
    ordering = ('order', 'name')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Основное', {
            'fields': (
                'name',
                'slug',
                'icon',
                'description',
            ),
        }),
        ('Отображение', {
            'fields': (
                'is_active',
                'order',
            ),
        }),
    )


# ======================================================================
#  EVENT IMAGE (отдельная страница — на случай, если нужно
#  редактировать вне события)
# ======================================================================

@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'event_link',
        'caption',
        'order',
        'preview',
    )
    list_filter = ('event',)
    search_fields = ('caption', 'event__title')
    ordering = ('event', 'order', 'id')
    list_per_page = 50
    list_select_related = ('event',)
    readonly_fields = ('preview',)

    @admin.display(description='Событие', ordering='event__title')
    def event_link(self, obj):
        return obj.event.title if obj.event else '—'

    @admin.display(description='Превью')
    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 60px; border-radius: 4px;">',
                obj.image.url,
            )
        return '—'


# ======================================================================
#  БРЕНДИНГ АДМИНКИ
# ======================================================================

admin.site.site_header = 'АФИША ИСКИТИМ'
admin.site.site_title = 'Афиша Искитим'
admin.site.index_title = 'Управление афишей'