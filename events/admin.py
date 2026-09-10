"""
Настройка админки для приложения events.

Jazzmin + стандартные возможности Django.
Оптимизация изображений — через easy-thumbnails.
"""

from datetime import timedelta

from django.contrib import admin
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from easy_thumbnails.files import get_thumbnailer

from .models import Event, Place, Category, Address, EventImage
from .models.models_analytics import PageView


# =========================================================
# ЦВЕТА СТАТУСОВ (для бейджей)
# =========================================================
STATUS_COLORS = {
    "draft":      ("#6b767a", "rgba(107, 118, 122, 0.12)"),
    "moderation": ("#d97706", "rgba(217, 119, 6, 0.12)"),
    "published":  ("#0f766e", "rgba(15, 118, 110, 0.12)"),
    "cancelled":  ("#dc2626", "rgba(220, 38, 38, 0.12)"),
    "finished":   ("#3d474b", "rgba(61, 71, 75, 0.10)"),
}


# =========================================================
# ХЕЛПЕР: генерация миниатюры
# =========================================================
def thumb_url(image, size, quality=85):
    """Возвращает URL миниатюры или None."""
    if not image:
        return None
    try:
        thumb = get_thumbnailer(image).get_thumbnail({
            "size": size,
            "crop": "smart",
            "quality": quality,
        })
        return thumb.url
    except Exception:
        return None


# =========================================================
# КАСТОМНЫЕ ФИЛЬТРЫ
# =========================================================
class EventPeriodFilter(admin.SimpleListFilter):
    """Быстрый фильтр по периоду для событий."""
    title = "Период"
    parameter_name = "period"

    def lookups(self, request, model_admin):
        return (
            ("today", "Сегодня"),
            ("week", "Ближайшие 7 дней"),
            ("month", "Ближайшие 30 дней"),
            ("past", "Прошедшие"),
        )

    def queryset(self, request, queryset):
        today = timezone.localdate()

        if self.value() == "today":
            return queryset.filter(start_date=today)
        if self.value() == "week":
            return queryset.filter(
                start_date__gte=today,
                start_date__lte=today + timedelta(days=7),
            )
        if self.value() == "month":
            return queryset.filter(
                start_date__gte=today,
                start_date__lte=today + timedelta(days=30),
            )
        if self.value() == "past":
            return queryset.filter(start_date__lt=today)
        return queryset


class HasImageFilter(admin.SimpleListFilter):
    """Фильтр: есть / нет картинки."""
    title = "Картинка"
    parameter_name = "has_image"

    def lookups(self, request, model_admin):
        return (
            ("yes", "С картинкой"),
            ("no", "Без картинки"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(main_image="")
        if self.value() == "no":
            return queryset.filter(main_image="")
        return queryset


class PageViewPeriodFilter(admin.SimpleListFilter):
    """Быстрый фильтр по периоду для статистики."""
    title = "Период"
    parameter_name = "period"

    def lookups(self, request, model_admin):
        return (
            ("today", "Сегодня"),
            ("week", "За 7 дней"),
            ("month", "За 30 дней"),
        )

    def queryset(self, request, queryset):
        today = timezone.localdate()

        if self.value() == "today":
            return queryset.filter(date=today)
        if self.value() == "week":
            return queryset.filter(date__gte=today - timedelta(days=7))
        if self.value() == "month":
            return queryset.filter(date__gte=today - timedelta(days=30))
        return queryset


# =========================================================
# INLINE: галерея изображений внутри формы события
# =========================================================
class EventImageInline(admin.TabularInline):
    """Галерея события — табличный inline."""

    model = EventImage
    extra = 1
    fields = ("image", "caption", "order", "preview_thumb")
    readonly_fields = ("preview_thumb",)
    ordering = ("order", "id")
    verbose_name = "Фото галереи"
    verbose_name_plural = "Галерея"

    @admin.display(description="Превью")
    def preview_thumb(self, obj):
        url = thumb_url(obj.image if obj.pk else None, (80, 60), quality=80)
        if not url:
            return "—"
        return format_html(
            '<img src="{}" style="width:80px;height:60px;'
            'object-fit:cover;border-radius:6px;" />',
            url,
        )


# =========================================================
# EVENT — основная модель
# =========================================================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Управление событиями."""

    list_display = (
        "title_short",
        "status_badge",
        "category",
        "start_date",
        "place_link",
        "price_display",
        "views_count",
        "image_preview_small",
    )
    list_display_links = ("title_short",)

    list_filter = (
        "status",
        "category",
        EventPeriodFilter,
        "is_free",
        HasImageFilter,
    )

    search_fields = (
        "title",
        "slug",
        "description",
        "description_short",
        "place__name",
        "contact_email",
        "contact_phone",
    )

    date_hierarchy = "start_date"
    ordering = ("-start_date", "-created_at")
    list_per_page = 50
    save_on_top = True
    show_full_result_count = True

    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        ("Основное", {
            "fields": (
                "title",
                "slug",
                ("category", "schedule_type"),
                "description_short",
                "description",
            ),
        }),
        ("Время и место", {
            "fields": (
                "place",
                ("start_date", "start_time", "end_date"),
            ),
        }),
        ("Цены и ограничения", {
            "fields": (
                ("is_free", "price"),
                "age_restriction",
            ),
        }),
        ("Медиа", {
            "fields": (
                "main_image",
                "image_preview_large",
            ),
        }),
        ("Контакты", {
            "classes": ("collapse",),
            "fields": (
                ("contact_phone", "contact_email"),
            ),
        }),
        ("Служебное", {
            "classes": ("collapse",),
            "fields": (
                "status",
                ("views_count", "favorites_count"),
            ),
        }),
    )

    readonly_fields = ("image_preview_large", "views_count", "favorites_count")

    inlines = (EventImageInline,)

    actions = (
        "make_published",
        "make_draft",
        "make_moderation",
        "make_cancelled",
    )

    # ---------- СПИСОК ----------

    @admin.display(description="Название", ordering="title")
    def title_short(self, obj):
        return (obj.title[:60] + "…") if len(obj.title) > 60 else obj.title

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        color, bg = STATUS_COLORS.get(
            obj.status,
            ("#6b767a", "rgba(107, 118, 122, 0.12)"),
        )
        return format_html(
            '<span style="display:inline-block;padding:3px 10px;'
            'border-radius:8px;font-size:11px;font-weight:600;'
            'color:{};background:{};white-space:nowrap;">{}</span>',
            color,
            bg,
            obj.get_status_display(),
        )

    @admin.display(description="Площадка", ordering="place__name")
    def place_link(self, obj):
        if not obj.place_id:
            return "—"
        url = reverse("admin:events_place_change", args=[obj.place_id])
        return format_html('<a href="{}">{}</a>', url, obj.place.name)

    @admin.display(description="Цена", ordering="price")
    def price_display(self, obj):
        if obj.is_free:
            return mark_safe(
                '<span style="color:#0f766e;font-weight:600;">Бесплатно</span>'
            )
        if obj.price:
            return f"{obj.price} ₽"
        return "—"

    @admin.display(description="Превью")
    def image_preview_small(self, obj):
        url = thumb_url(obj.main_image, (60, 40), quality=80)
        if not url:
            return "—"
        return format_html(
            '<img src="{}" style="width:60px;height:40px;'
            'object-fit:cover;border-radius:6px;" />',
            url,
        )

    @admin.display(description="Превью картинки")
    def image_preview_large(self, obj):
        if not obj.main_image:
            return mark_safe(
                '<div style="padding:16px;background:#f0f0f0;'
                'border-radius:8px;color:#888;font-size:13px;">'
                'Картинка не загружена</div>'
            )
        url = thumb_url(obj.main_image, (480, 320), quality=85)
        if not url:
            return "Картинка недоступна"
        return format_html(
            '<img src="{}" style="max-width:480px;max-height:320px;'
            'border-radius:8px;object-fit:cover;" />',
            url,
        )

    # ---------- ДЕЙСТВИЯ ----------

    @admin.action(description="Опубликовать")
    def make_published(self, request, queryset):
        updated = queryset.update(status=Event.Status.PUBLISHED)
        self.message_user(request, f"Опубликовано событий: {updated}")

    @admin.action(description="Вернуть в черновики")
    def make_draft(self, request, queryset):
        updated = queryset.update(status=Event.Status.DRAFT)
        self.message_user(request, f"Возвращено в черновики: {updated}")

    @admin.action(description="На модерацию")
    def make_moderation(self, request, queryset):
        updated = queryset.update(status=Event.Status.MODERATION)
        self.message_user(request, f"Отправлено на модерацию: {updated}")

    @admin.action(description="Отменить")
    def make_cancelled(self, request, queryset):
        updated = queryset.update(status=Event.Status.CANCELLED)
        self.message_user(request, f"Отменено событий: {updated}")


# =========================================================
# ADDRESS — адрес
# =========================================================
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Адреса. Связаны с площадкой через OneToOneField (Place.address)."""

    list_display = (
        "short_address_display",
        "city",
        "street",
        "house_number",
        "place_link",
    )
    list_display_links = ("short_address_display",)

    search_fields = (
        "city",
        "street",
        "house_number",
        "region",
        "postal_code",
        "landmark",
    )

    list_filter = ("country", "region", "city")
    ordering = ("city", "street", "house_number")

    fieldsets = (
        ("Основное", {
            "fields": (
                ("country", "region", "city"),
                "district",
                ("street", "house_number"),
                ("building", "office"),
                ("entrance", "floor"),
                "postal_code",
                "landmark",
            ),
        }),
        ("Координаты", {
            "classes": ("collapse",),
            "fields": (
                ("latitude", "longitude"),
            ),
        }),
    )

    @admin.display(description="Адрес", ordering="city")
    def short_address_display(self, obj):
        return obj.short_address or f"Адрес #{obj.pk}"

    @admin.display(description="Площадка")
    def place_link(self, obj):
        try:
            place = obj.place
        except Place.DoesNotExist:
            return "—"
        url = reverse("admin:events_place_change", args=[place.id])
        return format_html('<a href="{}">{}</a>', url, place.name)


# =========================================================
# PLACE — площадки
# =========================================================
@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    """Управление площадками."""

    list_display = (
        "name",
        "city_display",
        "address_link",
        "phone",
        "events_count",
        "image_preview_small",
    )
    list_display_links = ("name",)

    search_fields = (
        "name",
        "slug",
        "phone",
        "email",
        "address__city",
        "address__street",
    )

    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)

    fieldsets = (
        ("Основное", {
            "fields": (
                "name",
                "slug",
                "description",
            ),
        }),
        ("Контакты", {
            "fields": (
                ("phone", "email"),
                "website",
            ),
        }),
        ("Адрес", {
            "fields": (
                "address",
                "address_edit_link",
            ),
            "description": (
                "Адрес хранится в отдельной модели. "
                "Нажмите «Редактировать адрес», чтобы изменить улицу, дом, координаты."
            ),
        }),
        ("Медиа", {
            "fields": (
                "main_image",
                "image_preview_large",
            ),
        }),
    )

    readonly_fields = ("address_edit_link", "image_preview_large")

    @admin.display(description="Город", ordering="address__city")
    def city_display(self, obj):
        return obj.address.city if obj.address else "—"

    @admin.display(description="Адрес")
    def address_link(self, obj):
        if not obj.address:
            return "—"
        url = reverse("admin:events_address_change", args=[obj.address.id])
        return format_html('<a href="{}">{}</a>', url, obj.address.short_address)

    @admin.display(description="Событий")
    def events_count(self, obj):
        count = obj.events.count()
        if count == 0:
            return "0"
        url = reverse("admin:events_event_changelist") + f"?place__id__exact={obj.id}"
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description="Превью")
    def image_preview_small(self, obj):
        url = thumb_url(obj.main_image, (60, 40), quality=80)
        if not url:
            return "—"
        return format_html(
            '<img src="{}" style="width:60px;height:40px;'
            'object-fit:cover;border-radius:6px;" />',
            url,
        )

    @admin.display(description="Изменить адрес")
    def address_edit_link(self, obj):
        if not obj.address:
            return mark_safe(
                '<span style="color:#888;font-size:13px;">'
                'Адрес ещё не привязан. Сначала сохраните площадку, '
                'затем создайте адрес через раздел «Адреса» и привяжите его здесь.'
                '</span>'
            )
        url = reverse("admin:events_address_change", args=[obj.address.id])
        return format_html(
            '<a href="{}" style="display:inline-block;padding:8px 14px;'
            'background:#0f766e;color:#fff;border-radius:8px;'
            'text-decoration:none;font-weight:600;font-size:13px;">'
            'Редактировать адрес →</a>',
            url,
        )

    @admin.display(description="Превью картинки")
    def image_preview_large(self, obj):
        if not obj.main_image:
            return "Картинка не загружена"
        url = thumb_url(obj.main_image, (480, 320), quality=85)
        if not url:
            return "Картинка недоступна"
        return format_html(
            '<img src="{}" style="max-width:480px;max-height:320px;'
            'border-radius:8px;object-fit:cover;" />',
            url,
        )


# =========================================================
# CATEGORY — категории
# =========================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Управление категориями."""

    list_display = (
        "name",
        "slug",
        "icon_display",
        "events_count",
        "order",
        "is_active",
    )
    list_display_links = ("name",)
    list_editable = ("order", "is_active")

    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order", "name")

    fieldsets = (
        ("Основное", {
            "fields": (
                "name",
                "slug",
                "icon",
            ),
        }),
        ("Описание", {
            "fields": ("description",),
        }),
        ("Служебное", {
            "fields": (
                ("order", "is_active"),
            ),
        }),
    )

    @admin.display(description="Иконка")
    def icon_display(self, obj):
        return format_html('<code>{}</code>', obj.icon) if obj.icon else "—"

    @admin.display(description="Событий")
    def events_count(self, obj):
        count = obj.events.count()
        if count == 0:
            return "0"
        url = reverse("admin:events_event_changelist") + f"?category__id__exact={obj.id}"
        return format_html('<a href="{}">{}</a>', url, count)


# =========================================================
# EVENTIMAGE — галерея (отдельный раздел в админке)
# =========================================================
@admin.register(EventImage)
class EventImageAdmin(admin.ModelAdmin):
    """Все изображения галереи. Обычно редактируются через событие."""

    list_display = (
        "preview_thumb",
        "event_link",
        "caption",
        "order",
        "created_at",
    )
    list_display_links = ("preview_thumb",)

    list_filter = ("event",)
    search_fields = ("caption", "event__title")
    ordering = ("-created_at",)

    readonly_fields = ("preview_large",)

    @admin.display(description="Превью")
    def preview_thumb(self, obj):
        url = thumb_url(obj.image, (80, 60), quality=80)
        if not url:
            return "—"
        return format_html(
            '<img src="{}" style="width:80px;height:60px;'
            'object-fit:cover;border-radius:6px;" />',
            url,
        )

    @admin.display(description="Превью")
    def preview_large(self, obj):
        url = thumb_url(obj.image, (480, 320), quality=85)
        if not url:
            return "—"
        return format_html(
            '<img src="{}" style="max-width:480px;max-height:320px;'
            'border-radius:8px;object-fit:cover;" />',
            url,
        )

    @admin.display(description="Событие", ordering="event__title")
    def event_link(self, obj):
        if not obj.event_id:
            return "—"
        url = reverse("admin:events_event_change", args=[obj.event_id])
        return format_html('<a href="{}">{}</a>', url, obj.event.title)


# =========================================================
# PAGEVIEW — обезличенная статистика просмотров
# =========================================================
@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    """Обезличенная статистика просмотров. Только просмотр."""

    list_display = (
        "object_name_link",
        "kind_badge",
        "date",
        "count_display",
    )
    list_display_links = ("object_name_link",)

    list_filter = ("kind", PageViewPeriodFilter)

    ordering = ("-date", "-count")
    list_per_page = 100
    search_fields = ("object_id",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    # ---------- КОЛОНКИ ----------

    @admin.display(description="Объект", ordering="object_id")
    def object_name_link(self, obj):
        name = obj.get_object_name()
        url = self._get_object_url(obj)
        if url:
            return format_html('<a href="{}">{}</a>', url, name)
        return name

    @admin.display(description="Тип", ordering="kind")
    def kind_badge(self, obj):
        colors = {
            "event":    ("#0f766e", "rgba(15, 118, 110, 0.12)"),
            "place":    ("#3b82f6", "rgba(59, 130, 246, 0.12)"),
            "category": ("#d97706", "rgba(217, 119, 6, 0.12)"),
            "home":     ("#6b767a", "rgba(107, 118, 122, 0.12)"),
            "search":   ("#7c3aed", "rgba(124, 58, 237, 0.12)"),
        }
        color, bg = colors.get(obj.kind, ("#6b767a", "rgba(107, 118, 122, 0.12)"))
        return format_html(
            '<span style="display:inline-block;padding:3px 10px;'
            'border-radius:8px;font-size:11px;font-weight:600;'
            'color:{};background:{};white-space:nowrap;">{}</span>',
            color,
            bg,
            obj.get_kind_display(),
        )

    @admin.display(description="Просмотров", ordering="count")
    def count_display(self, obj):
        if obj.count >= 10:
            color = "#0f766e"
        elif obj.count >= 3:
            color = "#3d474b"
        else:
            color = "#6b767a"
        return format_html(
            '<strong style="color:{};">{}</strong>',
            color,
            obj.count,
        )

    def _get_object_url(self, obj):
        if not obj.object_id:
            return None
        try:
            if obj.kind == PageView.Kind.EVENT:
                return reverse("admin:events_event_change", args=[obj.object_id])
            if obj.kind == PageView.Kind.PLACE:
                return reverse("admin:events_place_change", args=[obj.object_id])
            if obj.kind == PageView.Kind.CATEGORY:
                return reverse("admin:events_category_change", args=[obj.object_id])
        except Exception:
            return None
        return None


# =========================================================
# ЗАГОЛОВКИ АДМИН-САЙТА
# =========================================================
admin.site.site_header = "Афиша Искитим"
admin.site.site_title = "Афиша Искитим — админка"
admin.site.index_title = "Панель управления"


# =========================================================
# КАСТОМНЫЙ ДАШБОРД ДЛЯ ГЛАВНОЙ АДМИНКИ
# =========================================================
def admin_dashboard_callback(request, context):
    """Статистика для главной страницы админки."""
    today = timezone.localdate()
    week_ahead = today + timedelta(days=7)
    since_7 = today - timedelta(days=7)

    # === ОБЩАЯ СТАТИСТИКА ===
    total_events = Event.objects.count()
    published = Event.objects.filter(status=Event.Status.PUBLISHED).count()
    drafts = Event.objects.filter(status=Event.Status.DRAFT).count()
    moderation = Event.objects.filter(status=Event.Status.MODERATION).count()
    past = Event.objects.filter(start_date__lt=today).count()

    # === БЛИЖАЙШИЕ СОБЫТИЯ (7 дней) ===
    upcoming = Event.objects.filter(
        status=Event.Status.PUBLISHED,
        start_date__gte=today,
        start_date__lte=week_ahead,
    ).order_by("start_date", "start_time")[:10]

    # === СУММЫ ПРОСМОТРОВ ===
    def _sum_views(kind, days=None):
        qs = PageView.objects.filter(kind=kind)
        if days is not None:
            since = today - timedelta(days=days)
            qs = qs.filter(date__gte=since)
        return qs.aggregate(total=Sum("count"))["total"] or 0

    total_views_7d = _sum_views("event", days=7)
    total_views_30d = _sum_views("event", days=30)
    total_views_all = _sum_views("event")

    # === ТОП-5 СОБЫТИЙ ЗА 7 ДНЕЙ ===
    top_events_7d_raw = (
        PageView.objects
        .filter(kind="event", date__gte=since_7, object_id__isnull=False)
        .values("object_id")
        .annotate(total=Sum("count"))
        .order_by("-total")[:5]
    )
    top_events_7d_ids = [r["object_id"] for r in top_events_7d_raw]
    top_events_7d_map = {r["object_id"]: r["total"] for r in top_events_7d_raw}
    top_events_7d = []
    if top_events_7d_ids:
        events_by_id = {e.id: e for e in Event.objects.filter(id__in=top_events_7d_ids)}
        for eid in top_events_7d_ids:
            if eid in events_by_id:
                top_events_7d.append({
                    "event": events_by_id[eid],
                    "views": top_events_7d_map[eid],
                })

    # === ТОП-5 КАТЕГОРИЙ ЗА 7 ДНЕЙ ===
    top_categories_7d_raw = (
        PageView.objects
        .filter(kind="category", date__gte=since_7, object_id__isnull=False)
        .values("object_id")
        .annotate(total=Sum("count"))
        .order_by("-total")[:5]
    )
    top_categories_7d_ids = [r["object_id"] for r in top_categories_7d_raw]
    top_categories_7d_map = {r["object_id"]: r["total"] for r in top_categories_7d_raw}
    top_categories_7d = []
    if top_categories_7d_ids:
        cats_by_id = {c.id: c for c in Category.objects.filter(id__in=top_categories_7d_ids)}
        for cid in top_categories_7d_ids:
            if cid in cats_by_id:
                top_categories_7d.append({
                    "category": cats_by_id[cid],
                    "views": top_categories_7d_map[cid],
                })

    # === КАТЕГОРИИ С ЧИСЛОМ СОБЫТИЙ ===
    categories_stats = Category.objects.annotate(
        event_count=Count("events")
    ).order_by("-event_count")[:10]

    # === ФИНАЛЬНЫЙ CONTEXT ===
    context.update({
        "dashboard": {
            "today": today,

            "total_events": total_events,
            "published": published,
            "drafts": drafts,
            "moderation": moderation,
            "past": past,

            "upcoming": upcoming,

            "total_places": Place.objects.count(),
            "total_categories": Category.objects.count(),
            "categories_stats": categories_stats,

            "total_views_7d": total_views_7d,
            "total_views_30d": total_views_30d,
            "total_views_all": total_views_all,

            "top_events_7d": top_events_7d,
            "top_categories_7d": top_categories_7d,
        }
    })
    return context