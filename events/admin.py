"""
Админка приложения events.

Регистрирует:
  • Event — список с фильтрами по статусу, категории, площадке;
  • Place — площадки;
  • Address — адреса;
  • Category — категории;
  • EventImage — галерея (инлайн в Event + отдельная страница);
  • ImportLog — журнал импортов.

Кнопка «Импортировать с kultisk.ru» рендерится через
templates/admin/base_site.html, который подхватывается автоматически.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Event,
    EventImage,
    Place,
    Address,
    Category,
    ImportLog,
)


# ======================================================================
#  БРЕНДИНГ АДМИНКИ
# ======================================================================

admin.site.site_header = 'АФИША ИСКИТИМ'
admin.site.site_title = 'Афиша Искитим'
admin.site.index_title = 'Управление афишей'


# ======================================================================
#  EVENT IMAGE (inline в Event)
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
        return (
            super().get_queryset(request)
            .select_related('category', 'place')
        )


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
        return super().get_queryset(request).select_related('address')


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
#  EVENT IMAGE (отдельная страница)
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
#  IMPORT LOG — только для просмотра
# ======================================================================

@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = (
        'started_at',
        'source',
        'status_display',
        'created_by',
        'events_created',
        'events_skipped',
        'rows_parsed',
        'duration',
    )
    list_filter = ('source', 'status')
    readonly_fields = (
        'source',
        'status',
        'started_at',
        'finished_at',
        'created_by',
        'events_created',
        'events_skipped',
        'rows_parsed',
        'rows_skipped',
        'log_output_pre',
    )
    fields = readonly_fields
    list_per_page = 50

    @admin.display(description='Статус', ordering='status')
    def status_display(self, obj):
        colors = {
            'running': '#6b767a',
            'success': '#0f766e',
            'error':   '#dc2626',
        }
        color = colors.get(obj.status, '#14181a')
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description='Длительность')
    def duration(self, obj):
        if not obj.finished_at:
            return '—'
        delta = obj.finished_at - obj.started_at
        return f'{delta.total_seconds():.1f} с'

    @admin.display(description='Вывод команды')
    def log_output_pre(self, obj):
        if not obj.log_output:
            return '—'
        return format_html(
            '<pre style="max-height: 600px; overflow: auto; '
            'background: #f7f9f8; padding: 12px; border-radius: 6px; '
            'font-size: 12px; line-height: 1.5; white-space: pre-wrap;">{}</pre>',
            obj.log_output,
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser