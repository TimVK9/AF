"""
Админка приложения events.

Регистрирует:
  • Event — список с фильтрами по статусу, категории, площадке;
  • Place — площадки (адрес внутри);
  • Category — категории;
  • EventImage — галерея (инлайн в Event + отдельная страница);
  • EventView, PlaceView, CategoryView, SiteView — аналитика;
  • ImportLog — журнал импортов.

Мягкое удаление: у всех моделей есть is_deleted. Через фильтр
«удаление» можно переключаться между активными и удалёнными.

Быстрые действия в списке Event:
  • 📢 Опубликовать выбранные;
  • 📝 Снять в черновики;
  • ⏳ Отправить на модерацию;
  • 🚫 Отменить;
  • ✅ Пометить завершёнными;
  • Пометить как удалённые;
  • Восстановить.
"""

from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html

from .models import (
    Event,
    EventImage,
    Place,
    Category,
    EventView,
    PlaceView,
    CategoryView,
    SiteView,
    ImportLog,
)


# ======================================================================
#  БРЕНДИНГ АДМИНКИ
# ======================================================================

admin.site.site_header = 'АФИША ИСКИТИМ'
admin.site.site_title = 'Афиша Искитим'
admin.site.index_title = 'Управление афишей'


# ======================================================================
#  МИКСИНЫ И ФИЛЬТРЫ
# ======================================================================

class SoftDeleteAdminMixin:
    """
    Действия «Пометить удалёнными» и «Восстановить».
    Не задаёт actions — складывается с другими миксинами.
    """

    @admin.action(description='🗑 Пометить как удалённые')
    def soft_delete_selected(self, request, queryset):
        count = 0
        for obj in queryset:
            if not obj.is_deleted:
                obj.delete()
                count += 1
        self.message_user(request, f'Помечено удалёнными: {count}')

    @admin.action(description='↩ Восстановить')
    def restore_selected(self, request, queryset):
        count = 0
        for obj in queryset:
            if obj.is_deleted:
                obj.restore()
                count += 1
        self.message_user(request, f'Восстановлено: {count}')


class EventStatusActionsMixin:
    """Быстрые действия для массовой смены статуса события."""

    @admin.action(description='📢 Опубликовать выбранные')
    def action_publish(self, request, queryset):
        updated = queryset.update(status=Event.Status.PUBLISHED)
        self.message_user(request, f'Опубликовано: {updated}')

    @admin.action(description='📝 Снять в черновики')
    def action_draft(self, request, queryset):
        updated = queryset.update(status=Event.Status.DRAFT)
        self.message_user(request, f'Снято в черновики: {updated}')

    @admin.action(description='⏳ Отправить на модерацию')
    def action_moderation(self, request, queryset):
        updated = queryset.update(status=Event.Status.MODERATION)
        self.message_user(request, f'Отправлено на модерацию: {updated}')

    @admin.action(description='🚫 Отменить')
    def action_cancel(self, request, queryset):
        updated = queryset.update(status=Event.Status.CANCELLED)
        self.message_user(request, f'Отменено: {updated}')

    @admin.action(description='✅ Пометить завершёнными')
    def action_finish(self, request, queryset):
        updated = queryset.update(status=Event.Status.FINISHED)
        self.message_user(request, f'Помечено завершёнными: {updated}')


class DeletedFilter(admin.SimpleListFilter):
    """Фильтр «удаление» в правой колонке."""
    title = 'удаление'
    parameter_name = 'is_deleted'

    def lookups(self, request, model_admin):
        return (
            ('no', 'Только активные'),
            ('yes', 'Только удалённые'),
            ('all', 'Все'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(is_deleted=True)
        if self.value() == 'all':
            return queryset
        return queryset.filter(is_deleted=False)


# ======================================================================
#  EVENT IMAGE (inline)
# ======================================================================

class EventImageInline(admin.TabularInline):
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
class EventAdmin(EventStatusActionsMixin, SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'place',
        'start_date',
        'end_date',
        'status',
        'is_free',
        'price',
        'views_total',
        'is_deleted_flag',
    )
    list_filter = (
        'status',
        'is_free',
        'category',
        'place',
        'age_restriction',
        'start_date',
        DeletedFilter,
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

    readonly_fields = ('created_at', 'updated_at')

    actions = (
        'action_publish',
        'action_draft',
        'action_moderation',
        'action_cancel',
        'action_finish',
        'soft_delete_selected',
        'restore_selected',
    )

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
        ('Служебное', {
            'classes': ('collapse',),
            'fields': (
                'is_deleted',
                ('created_at', 'updated_at'),
            ),
        }),
    )

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('title',)}

    def get_queryset(self, request):
        qs = self.model.all_objects.select_related('category', 'place')
        qs = qs.annotate(views_total_sum=Sum('views__count'))
        return qs

    @admin.display(description='Просмотры', ordering='views_total_sum')
    def views_total(self, obj):
        return obj.views_total_sum or 0

    @admin.display(description='Удалено', boolean=True)
    def is_deleted_flag(self, obj):
        return obj.is_deleted


# ======================================================================
#  PLACE (адрес внутри)
# ======================================================================

@admin.register(Place)
class PlaceAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'city',
        'short_address_display',
        'phone',
        'email',
        'is_deleted_flag',
    )
    search_fields = (
        'name',
        'description',
        'phone',
        'email',
        'city',
        'street',
    )
    list_filter = ('city', DeletedFilter)
    ordering = ('name',)
    list_per_page = 30
    prepopulated_fields = {'slug': ('name',)}

    actions = (
        'soft_delete_selected',
        'restore_selected',
    )

    fieldsets = (
        ('Основное', {
            'fields': (
                'name',
                'slug',
                'description',
                'main_image',
            ),
        }),
        ('Адрес', {
            'fields': (
                ('city', 'street', 'house_number'),
                ('building', 'office', 'entrance'),
                ('floor', 'landmark', 'postal_code'),
            ),
        }),
        ('Координаты', {
            'fields': (
                ('latitude', 'longitude'),
            ),
        }),
        ('Контакты', {
            'fields': ('website', 'phone', 'email', 'vk_url'),
        }),
        ('Служебное', {
            'classes': ('collapse',),
            'fields': ('is_deleted',),
        }),
    )

    def get_queryset(self, request):
        return self.model.all_objects.all()

    @admin.display(description='Адрес')
    def short_address_display(self, obj):
        return obj.short_address or '—'

    @admin.display(description='Удалено', boolean=True)
    def is_deleted_flag(self, obj):
        return obj.is_deleted


# ======================================================================
#  CATEGORY
# ======================================================================

@admin.register(Category)
class CategoryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        'name',
        'slug',
        'icon',
        'is_active',
        'order',
        'is_deleted_flag',
    )
    list_filter = ('is_active', DeletedFilter)
    search_fields = ('name', 'slug', 'description')
    ordering = ('order', 'name')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}

    actions = (
        'soft_delete_selected',
        'restore_selected',
    )

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
        ('Служебное', {
            'classes': ('collapse',),
            'fields': ('is_deleted',),
        }),
    )

    def get_queryset(self, request):
        return self.model.all_objects.all()

    @admin.display(description='Удалено', boolean=True)
    def is_deleted_flag(self, obj):
        return obj.is_deleted


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
#  АНАЛИТИКА — только для просмотра
# ======================================================================

class BaseViewAdmin(admin.ModelAdmin):
    list_per_page = 50
    date_hierarchy = 'date'
    ordering = ('-date',)
    list_filter = ('date',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(EventView)
class EventViewAdmin(BaseViewAdmin):
    list_display = ('event', 'date', 'count')
    search_fields = ('event__title',)
    list_select_related = ('event',)
    readonly_fields = ('event', 'date', 'count')


@admin.register(PlaceView)
class PlaceViewAdmin(BaseViewAdmin):
    list_display = ('place', 'date', 'count')
    search_fields = ('place__name',)
    list_select_related = ('place',)
    readonly_fields = ('place', 'date', 'count')


@admin.register(CategoryView)
class CategoryViewAdmin(BaseViewAdmin):
    list_display = ('category', 'date', 'count')
    search_fields = ('category__name',)
    list_select_related = ('category',)
    readonly_fields = ('category', 'date', 'count')


@admin.register(SiteView)
class SiteViewAdmin(BaseViewAdmin):
    list_display = ('kind', 'date', 'count')
    list_filter = ('kind', 'date')
    readonly_fields = ('kind', 'date', 'count')


# ======================================================================
#  IMPORT LOG
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
        'duration_display',
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
    date_hierarchy = 'started_at'

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
    def duration_display(self, obj):
        d = obj.duration
        if d is None:
            return '—'
        return f'{d:.1f} с'

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