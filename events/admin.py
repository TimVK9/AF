"""
Админка приложения events.
"""
from django.contrib import admin
from django.db.models import Sum
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    Event,
    EventImage,
    Place,
    Category,
    EventView,
    PlaceView,
    CategoryView,
    SiteView,
    EmailOTP,
    ImportLog,
    SiteSettings,
)


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
        'title',
        'organizer_name',
        'category',
        'place',
        'start_date',
        'status_badge',
        'views_count',
        'created_at',
    )
    list_filter = (
        'status',
        'category',
        'place',
        'age_restriction',
        'is_free',
        'start_date',
        'is_deleted',
    )
    search_fields = (
        'title',
        'description_short',
        'description',
        'organizer_name',
        'organizer_email',
        'organizer_phone',
        'place__name',
    )
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    ordering = ('-start_date', '-created_at')
    save_on_top = True
    inlines = [EventImageInline]
    list_per_page = 30

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
            'fields': ('status', 'age_restriction'),
        }),
        ('Дата и время', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time'),
        }),
        ('Цена', {
            'fields': ('is_free', 'price'),
        }),
        ('Медиа', {
            'fields': ('main_image', 'main_image_preview'),
        }),
        ('Организатор', {
            'fields': (
                'organizer_name',
                'organizer_email',
                'organizer_phone',
                'organizer_vk',
            ),
        }),
        ('Счётчики', {
            'fields': ('views_count', 'favorites_count'),
            'classes': ('collapse',),
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
            color,
            color,
            obj.get_status_display(),
        )

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related('category', 'place')
        )


# =====================================================================
#  ГАЛЕРЕЯ
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
                'building', 'office', 'entrance', 'floor',
                'landmark', 'postal_code',
            ),
        }),
        ('Координаты', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',),
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
        return obj.events.count()


# =====================================================================
#  EMAIL-КОДЫ
# =====================================================================
@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email', 'code')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'expires_at')

    def has_add_permission(self, request):
        return False


# =====================================================================
#  ИМПОРТЫ
# =====================================================================
@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = (
        'source', 'status', 'started_at', 'finished_at',
        'events_created', 'events_skipped', 'created_by',
    )
    list_filter = ('source', 'status')
    search_fields = ('log_output',)
    ordering = ('-started_at',)
    readonly_fields = (
        'source', 'status', 'started_at', 'finished_at',
        'created_by', 'events_created', 'events_skipped',
        'rows_parsed', 'rows_skipped', 'log_output',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# =====================================================================
#  АНАЛИТИКА — ТОЛЬКО ЧТЕНИЕ
# =====================================================================
class AbstractViewAdmin(admin.ModelAdmin):
    """Базовая админка для дневных счётчиков просмотров."""
    list_filter = ('date',)
    ordering = ('-date',)
    date_hierarchy = 'date'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EventView)
class EventViewAdmin(AbstractViewAdmin):
    list_display = ('event', 'date', 'count')
    search_fields = ('event__title',)


@admin.register(PlaceView)
class PlaceViewAdmin(AbstractViewAdmin):
    list_display = ('place', 'date', 'count')
    search_fields = ('place__name',)


@admin.register(CategoryView)
class CategoryViewAdmin(AbstractViewAdmin):
    list_display = ('category', 'date', 'count')
    search_fields = ('category__name',)


@admin.register(SiteView)
class SiteViewAdmin(AbstractViewAdmin):
    list_display = ('kind', 'date', 'count')
    list_filter = ('kind', 'date')


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
            return format_html(
                '<span style="display:inline-block;padding:3px 10px;'
                'border-radius:10px;background:rgba(220,38,38,0.15);'
                'color:#b91c1c;font-weight:700;font-size:11px;'
                'text-transform:uppercase;">{}</span>',
                'Включено',
            )
        return format_html(
            '<span style="display:inline-block;padding:3px 10px;'
            'border-radius:10px;background:rgba(15,118,110,0.15);'
            'color:#0f766e;font-weight:700;font-size:11px;'
            'text-transform:uppercase;">{}</span>',
            'Выключено',
        )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        """
        Создаём синглтон при первом открытии списка, чтобы не было
        пустой страницы.
        """
        SiteSettings.load()
        return super().changelist_view(request, extra_context)


# =====================================================================
#  КАСТОМНЫЙ ДАШБОРД
# =====================================================================
def admin_dashboard_callback(request, extra_context):
    """Дополняет главную админки плитками со статистикой."""
    today = timezone.localdate()

    extra_context['events_total'] = Event.objects.count()
    extra_context['events_published'] = Event.objects.filter(
        status=Event.Status.PUBLISHED
    ).count()
    extra_context['events_draft'] = Event.objects.filter(
        status=Event.Status.DRAFT
    ).count()
    extra_context['events_moderation'] = Event.objects.filter(
        status=Event.Status.MODERATION
    ).count()
    extra_context['events_today'] = Event.objects.filter(
        start_date=today,
        status=Event.Status.PUBLISHED,
    ).count()
    extra_context['events_upcoming'] = Event.objects.filter(
        start_date__gte=today,
        status=Event.Status.PUBLISHED,
    ).count()
    extra_context['places_total'] = Place.objects.count()
    extra_context['categories_total'] = Category.objects.count()

    extra_context['top_events'] = (
        Event.objects
        .filter(status=Event.Status.PUBLISHED)
        .order_by('-views_count')[:5]
    )

    week_ago = today - timezone.timedelta(days=7)
    extra_context['views_week'] = (
        EventView.objects
        .filter(date__gte=week_ago)
        .aggregate(total=Sum('count'))
    )['total'] or 0

    extra_context['url_event_manage'] = reverse('events:event_list_manage')
    extra_context['url_event_create'] = reverse('events:event_create')

    # Статус заглушки для дашборда
    try:
        extra_context['site_settings'] = SiteSettings.load()
    except Exception:
        extra_context['site_settings'] = None