"""
Функции обезличенной статистики просмотров.

Использует модели EventView / PlaceView / CategoryView / SiteView
из events.models.analytics.

Принцип: НЕ сохраняем ПДн. Только «сколько раз за день посмотрели объект X».
Никаких IP, User-Agent, cookies, session_id.
"""
from datetime import timedelta

from django.db.models import F, Sum
from django.utils import timezone

from .models import EventView, PlaceView, CategoryView, SiteView


# Соответствие kind → (модель, поле-внешний ключ)
_MODEL_MAP = {
    'event': (EventView, 'event_id'),
    'place': (PlaceView, 'place_id'),
    'category': (CategoryView, 'category_id'),
}


def track_view(kind, object_id=0):
    """
    Увеличивает счётчик просмотров на 1 за сегодня.

    kind: 'event' | 'place' | 'category' | 'home' | 'search'
    object_id: id объекта; для 'home' и 'search' не используется.
    """
    today = timezone.localdate()

    # --- event / place / category ---
    if kind in _MODEL_MAP:
        model, field = _MODEL_MAP[kind]
        filters = {field: object_id, 'date': today}
        updated = model.objects.filter(**filters).update(count=F('count') + 1)
        if not updated:
            try:
                model.objects.create(**filters, count=1)
            except Exception:
                # Гонка — кто-то успел создать. Просто инкрементим.
                model.objects.filter(**filters).update(count=F('count') + 1)
        return

    # --- home / search ---
    if kind in ('home', 'search'):
        filters = {'kind': kind, 'date': today}
        updated = SiteView.objects.filter(**filters).update(count=F('count') + 1)
        if not updated:
            try:
                SiteView.objects.create(**filters, count=1)
            except Exception:
                SiteView.objects.filter(**filters).update(count=F('count') + 1)
        return


def get_event_total_views(event_id, days=None):
    """
    Сумма всех просмотров события.
    Если days указан — только за последние N дней.
    """
    qs = EventView.objects.filter(event_id=event_id)
    if days:
        since = timezone.localdate() - timedelta(days=days)
        qs = qs.filter(date__gte=since)
    return qs.aggregate(total=Sum('count'))['total'] or 0


def get_place_total_views(place_id, days=None):
    """Сумма просмотров площадки."""
    qs = PlaceView.objects.filter(place_id=place_id)
    if days:
        since = timezone.localdate() - timedelta(days=days)
        qs = qs.filter(date__gte=since)
    return qs.aggregate(total=Sum('count'))['total'] or 0


def get_category_total_views(category_id, days=None):
    """Сумма просмотров категории."""
    qs = CategoryView.objects.filter(category_id=category_id)
    if days:
        since = timezone.localdate() - timedelta(days=days)
        qs = qs.filter(date__gte=since)
    return qs.aggregate(total=Sum('count'))['total'] or 0


def get_site_total_views(kind, days=None):
    """Сумма просмотров главной или поиска."""
    qs = SiteView.objects.filter(kind=kind)
    if days:
        since = timezone.localdate() - timedelta(days=days)
        qs = qs.filter(date__gte=since)
    return qs.aggregate(total=Sum('count'))['total'] or 0