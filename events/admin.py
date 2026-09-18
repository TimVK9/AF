"""Админка приложения events."""
from django.contrib import admin

from .models import Category, Place, Event, EventImage, WorkingSeason


class EventImageInline(admin.TabularInline):
    """Галерея внутри карточки события."""
    model = EventImage
    extra = 1
    fields = ('image', 'caption', 'order')
    ordering = ('order', 'id')


class WorkingSeasonInline(admin.StackedInline):
    """Сезоны работы площадки — галочки дней недели и выпадающие месяцы."""
    model = WorkingSeason
    extra = 0
    fields = (
        'name',
        ('start_month', 'start_day'),
        ('end_month', 'end_day'),
        ('open_mon', 'open_tue', 'open_wed'),
        ('open_thu', 'open_fri', 'open_sat', 'open_sun'),
        'time',
        'order',
    )
    verbose_name = 'Сезон работы'
    verbose_name_plural = 'Сезоны работы'
    ordering = ('order', 'id')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_active', 'order', 'status', 'created_at')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active', 'status', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('order', 'name')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'street', 'house_number', 'latitude', 'longitude', 'status', 'created_at')
    list_filter = ('city', 'status', 'created_at')
    search_fields = ('name', 'city', 'street', 'house_number', 'phone', 'email')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [WorkingSeasonInline]
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'description', 'status', 'main_image'),
        }),
        ('Контакты', {
            'fields': ('phone', 'email', 'website', 'vk_url'),
        }),
        ('Адрес', {
            'fields': (
                'city', 'street', 'house_number', 'building',
                'office', 'floor', 'postal_code',  'latitude', 'longitude',
            ),
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'place', 'category', 'start_date', 'end_date',
        'status', 'price', 'age_restriction', 'updated_at',
    )
    list_filter = (
        'status', 'age_restriction', 'category', 'place',
        'start_date', 'created_at',
    )
    search_fields = ('title', 'description_short', 'description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    ordering = ('-start_date', '-start_time')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [EventImageInline]
    autocomplete_fields = ('place', 'category')
    list_select_related = ('place', 'category')
    fieldsets = (
        ('Основное', {
            'fields': (
                'title', 'slug', 'category', 'place',
                'description_short', 'description',
                'status', 'age_restriction', 'main_image',
            ),
        }),
        ('Даты и время', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time'),
        }),
        ('Цена и билеты', {
            'fields': ('price', 'external_url'),
        }),
        ('Организатор', {
            'fields': (
                'organizer_name', 'organizer_email',
                'organizer_phone', 'organizer_vk',
            ),
        }),
        ('Служебное', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    actions = ('action_publish', 'action_moderation', 'action_draft')

    @admin.action(description='Опубликовать выбранные')
    def action_publish(self, request, queryset):
        updated = queryset.update(status=Event.Status.PUBLISHED)
        self.message_user(request, f'Опубликовано: {updated}')

    @admin.action(description='Отправить на модерацию')
    def action_moderation(self, request, queryset):
        updated = queryset.update(status=Event.Status.MODERATION)
        self.message_user(request, f'Отправлено на модерацию: {updated}')

    @admin.action(description='Снять в черновики')
    def action_draft(self, request, queryset):
        updated = queryset.update(status=Event.Status.DRAFT)
        self.message_user(request, f'Снято в черновики: {updated}')


@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'caption', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('caption', 'event__title')
    autocomplete_fields = ('event',)
    ordering = ('event', 'order', 'id')
    readonly_fields = ('created_at', 'updated_at')
