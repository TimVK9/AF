"""
Обезличенная внутренняя статистика.

Инкремент через UPSERT — `bulk_create(ignore_conflicts=True)`.
Никаких ПДн.
"""
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import EventView, PlaceView, CategoryView, SiteView


def track_view(kind: str, object_id: int = None) -> None:
    """
    Увеличивает счётчик просмотров за сегодня.

    kind:
      • 'event'    — object_id = pk события;
      • 'place'    — object_id = pk площадки;
      • 'category' — object_id = pk категории;
      • 'home'     — object_id игнорируется;
      • 'search'   — object_id игнорируется.
    """
    today = timezone.localdate()

    if kind == 'event':
        _bump(EventView, event_id=object_id, date=today)
    elif kind == 'place':
        _bump(PlaceView, place_id=object_id, date=today)
    elif kind == 'category':
        _bump(CategoryView, category_id=object_id, date=today)
    elif kind == 'home':
        _bump(SiteView, kind=SiteView.Kind.HOME, date=today)
    elif kind == 'search':
        _bump(SiteView, kind=SiteView.Kind.SEARCH, date=today)
    else:
        raise ValueError(f'Неизвестный kind: {kind!r}')


def _bump(model, date, **kwargs):
    """Атомарный UPSERT: инкремент или создание записи с count=1."""
    # Попытка инкремента
    updated = model.objects.filter(date=date, **kwargs).update(
        count=F('count') + 1
    )
    if updated:
        return

    # Создание — с игнором конфликтов, если параллельный запрос успел
    created = model.objects.bulk_create(
        [model(date=date, count=1, **kwargs)],
        ignore_conflicts=True,
    )
    if not created:
        # Гонка — запись уже есть, инкрементим
        model.objects.filter(date=date, **kwargs).update(
            count=F('count') + 1
        )


# ======================================================================
#  Аналитика: топы и сводки
# ======================================================================

def get_event_total_views(event_id: int, days: int = None) -> int:
    """Суммарные просмотры события. days=None — за всё время."""
    qs = EventView.objects.filter(event_id=event_id)
    if days:
        since = timezone.localdate() - timezone.timedelta(days=days)
        qs = qs.filter(date__gte=since)
    return qs.aggregate(total=Sum('count'))['total'] or 0


def get_top_events(days: int = 7, limit: int = 10):
    """Топ-N событий по просмотрам за последние `days` дней."""
    since = timezone.localdate() - timezone.timedelta(days=days)
    return (
        EventView.objects
        .filter(date__gte=since)
        .values('event_id')
        .annotate(total=Sum('count'))
        .order_by('-total')[:limit]
    )


def get_daily_views(model, days: int = 30, **filters):
    """Список (дата, сумма) за последние `days` дней."""
    since = timezone.localdate() - timezone.timedelta(days=days)
    rows = (
        model.objects
        .filter(date__gte=since, **filters)
        .values('date')
        .annotate(total=Sum('count'))
        .order_by('date')
    )
    return [(row['date'], row['total']) for row in rows]