"""
Админка приложения events.

Совместимо с Django 5.x и 6.x.

ПРАВИЛА (иначе падает):
1. format_html() требует args или kwargs.
   - Нужны подстановки → format_html('...{}...', value)
   - Подстановок нет   → mark_safe('...')
2. Event.objects скрывает мягко удалённые (SoftDeleteManager).
   Чтобы видеть корзину — используем Event.all_objects.
3. Поля schedule_type, is_free, views_count, favorites_count,
   latitude, longitude, landmark, entrance — НЕ существуют
   в моделях. Не добавлять.
"""
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Event, EventImage, Place, Category, SiteSettings


# =====================================================================
#  INLINE: ГАЛЕРЕЯ ИЗОБРАЖЕНИЙ
# =====================================================================
class EventImageInline(admin.TabularInline):
    """Inline-галерея изображений внутри карточки события."""
    model = EventImage
    extra = 1
    fields = ('image', 'caption', 'order', 'preview')
    readonly_fields = ('preview',)
    ordering = ('order', 'id')

    @admin.display(description='Превью')
    def preview(self, obj):
        if not obj.image:
            return '—'
        return format_html(
            '<img src="{}" style="height:60px;border-radius:6px;" />',
            obj.image.url,
        )


# =====================================================================
#  СОБЫТИЕ
# =====================================================================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'organizer_name', 'category', 'place',
        'start_date', 'status_badge', 'deleted_badge', 'created_at',
    )
    list_filter = (
        'status', 'category', 'place', 'age_restriction',
        'start_date', 'is_deleted',
    )
    search_fields = (
        'title', 'description_short', 'description',
        'organizer_name', 'organizer_email', 'organizer_phone', 'place__name',
    )
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    ordering = ('-start_date', '-created_at')
    save_on_top = True
    inlines = [EventImageInline]
    list_per_page = 30

    actions = (
        'action_publish',
        'action_draft',
        'action_cancel',
        'action_soft_delete',
        'action_restore',
    )

    fieldsets = (
        ('Основное', {
            'fields': (
                'title', 'slug', 'category', 'place',
                'description_short', 'description',
            ),
        }),
        ('Статус и ограничения', {
            'fields': ('status', 'age_restriction'),
        }),
        ('Дата и время', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time'),
        }),
        ('Цена', {
            'fields': ('price',),
            'description': (
                'Оставьте пустым, если цена «уточняется». '
                'Если цена 0 — событие считается бесплатным.'
            ),
        }),
        ('Медиа', {
            'fields': ('main_image', 'main_image_preview'),
        }),
        ('Организатор', {
            'fields': (
                'organizer_name', 'organizer_email',
                'organizer_phone', 'organizer_vk',
            ),
        }),
        ('Служебное', {
            'fields': ('is_deleted',),
            'classes': ('collapse',),
            'description': (
                'Поле is_deleted управляется мягким удалением. '
                'Меняйте вручную только при необходимости.'
            ),
        }),
    )

    readonly_fields = ('main_image_preview',)

    @admin.display(description='Превью')
    def main_image_preview(self, obj):
        if not obj.main_image:
            return '—'
        return format_html(
            '<img src="{}" style="max-height:200px;border-radius:8px;" />',
            obj.main_image.url,
        )

    @admin.display(description='Статус', ordering='status')
    def status_badge(self, obj):
        colors = {
            'draft': '#6b767a',
            'moderation': '#b45309',
            'published': '#0f766e',
            'cancelled': '#b91c1c',
            'finished': '#14181a',
        }
        color = colors.get(obj.status, '#6b767a')
        return format_html(
            '<span style="display:inline-block;padding:3px 10px;'
            'border-radius:10px;background:{}20;color:{};font-size:11px;'
            'font-weight:700;text-transform:uppercase;letter-spacing:0.3px;">'
            '{}</span>',
            color, color, obj.get_status_display(),
        )

    @admin.display(description='В корзине', ordering='is_deleted')
    def deleted_badge(self, obj):
        if obj.is_deleted:
            return mark_safe(
                '<span style="display:inline-block;padding:2px 8px;'
                'border-radius:8px;background:rgba(220,38,38,0.15);'
                'color:#b91c1c;font-size:11px;font-weight:700;'
                'text-transform:uppercase;">В корзине</span>'
            )
        return '—'

    @admin.action(description='Опубликовать выбранные')
    def action_publish(self, request, queryset):
        updated = queryset.filter(is_deleted=False).update(
            status=Event.Status.PUBLISHED
        )
        self.message_user(
            request, f'Опубликовано: {updated}.', level=messages.SUCCESS,
        )

    @admin.action(description='Снять в черновики')
    def action_draft(self, request, queryset):
        updated = queryset.filter(is_deleted=False).update(
            status=Event.Status.DRAFT
        )
        self.message_user(
            request, f'Снято в черновики: {updated}.', level=messages.SUCCESS,
        )

    @admin.action(description='Отменить выбранные')
    def action_cancel(self, request, queryset):
        updated = queryset.filter(is_deleted=False).update(
            status=Event.Status.CANCELLED
        )
        self.message_user(
            request, f'Отменено: {updated}.', level=messages.SUCCESS,
        )

    @admin.action(description='Удалить в корзину (мягко)')
    def action_soft_delete(self, request, queryset):
        count = queryset.filter(is_deleted=False).update(
            is_deleted=True,
            status=Event.Status.DRAFT,
        )
        self.message_user(
            request, f'Удалено в корзину: {count}.', level=messages.SUCCESS,
        )

    @admin.action(description='Восстановить из корзины')
    def action_restore(self, request, queryset):
        count = queryset.filter(is_deleted=True).update(is_deleted=False)
        self.message_user(
            request, f'Восстановлено: {count}.', level=messages.SUCCESS,
        )

    def get_queryset(self, request):
        return (
            Event.all_objects
            .select_related('category', 'place')
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


# =====================================================================
#  ГАЛЕРЕЯ (отдельная страница)
# =====================================================================
@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'caption', 'order', 'preview')
    list_filter = ('event',)
    search_fields = ('caption', 'event__title')
    ordering = ('event', 'order', 'id')
    readonly_fields = ('preview',)

    @admin.display(description='Превью')
    def preview(self, obj):
        if not obj.image:
            return '—'
        return format_html(
            '<img src="{}" style="height:60px;border-radius:6px;" />',
            obj.image.url,
        )


# =====================================================================
#  ПЛОЩАДКА
# =====================================================================
@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'city', 'street', 'house_number',
        'phone', 'main_image_preview',
    )
    search_fields = ('name', 'city', 'street', 'house_number')
    list_filter = ('city',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'description'),
        }),
        ('Контакты', {
            'fields': ('website', 'phone', 'vk_url', 'email'),
        }),
        ('Адрес', {
            'fields': (
                'city', 'street', 'house_number',
                'building', 'office', 'floor', 'postal_code',
            ),
        }),
        ('Медиа', {
            'fields': ('main_image', 'main_image_preview'),
        }),
    )
    readonly_fields = ('main_image_preview',)

    @admin.display(description='Фото')
    def main_image_preview(self, obj):
        if not obj.main_image:
            return '—'
        return format_html(
            '<img src="{}" style="height:60px;border-radius:6px;" />',
            obj.main_image.url,
        )


# =====================================================================
#  КАТЕГОРИЯ
# =====================================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active', 'events_count')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')

    @admin.display(description='Событий')
    def events_count(self, obj):
        return obj.events.filter(is_deleted=False).count()


# =====================================================================
#  НАСТРОЙКИ САЙТА (СИНГЛТОН)
# =====================================================================
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('coming_soon_badge', 'updated_at')
    readonly_fields = ('updated_at',)

    fieldsets = (
        ('Режим заглушки', {
            'fields': ('coming_soon', 'coming_soon_message'),
            'description': (
                'Включите «Скоро запуск», чтобы все посетители '
                '(кроме staff и superuser) видели страницу-заглушку. '
                'Админы видят сайт как обычно.'
            ),
        }),
        ('Служебное', {
            'fields': ('updated_at',),
        }),
    )

    @admin.display(description='Заглушка')
    def coming_soon_badge(self, obj):
        if obj.coming_soon:
            return mark_safe(
                '<span style="display:inline-block;padding:3px 10px;'
                'border-radius:10px;background:rgba(220,38,38,0.15);'
                'color:#b91c1c;font-weight:700;font-size:11px;'
                'text-transform:uppercase;">Включено</span>'
            )
        return mark_safe(
            '<span style="display:inline-block;padding:3px 10px;'
            'border-radius:10px;background:rgba(15,118,110,0.15);'
            'color:#0f766e;font-weight:700;font-size:11px;'
            'text-transform:uppercase;">Выключено</span>'
        )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        SiteSettings.load()
        return super().changelist_view(request, extra_context)