"""
Обезличенная внутренняя статистика.

Принцип: инкремент счётчика через атомарный UPSERT.
Не сохраняем ПДн — ни IP, ни cookies, ни User-Agent.
"""
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone

from .models.models_analytics import PageView


def track_view(kind: str, object_id: int = None):
    """
    Увеличивает счётчик просмотров на 1 для пары (kind, object_id) на сегодня.

    kind: "event" | "place" | "category" | "home" | "search"
    object_id: ID объекта (None для главной/поиска)
    """
    today = timezone.localdate()

    with transaction.atomic():
        updated = PageView.objects.filter(
            kind=kind,
            object_id=object_id,
            date=today,
        ).update(count=F("count") + 1)

        if not updated:
            try:
                PageView.objects.create(
                    kind=kind,
                    object_id=object_id,
                    date=today,
                    count=1,
                )
            except Exception:
                # Гонка — параллельный запрос успел создать. Просто инкрементим.
                PageView.objects.filter(
                    kind=kind,
                    object_id=object_id,
                    date=today,
                ).update(count=F("count") + 1)


def get_top(kind: str, days: int = 7, limit: int = 10):
    """Топ-N объектов за последние `days` дней (сумма счётчиков)."""
    since = timezone.localdate() - timezone.timedelta(days=days)

    return (
        PageView.objects
        .filter(kind=kind, date__gte=since, object_id__isnull=False)
        .values("object_id")
        .annotate(total=models.Sum("count"))
        .order_by("-total")[:limit]
    )


def get_daily_stats(kind: str, days: int = 30):
    """Список (дата, сумма просмотров) за последние `days` дней."""
    since = timezone.localdate() - timezone.timedelta(days=days)

    rows = (
        PageView.objects
        .filter(kind=kind, date__gte=since)
        .values("date")
        .annotate(total=models.Sum("count"))
        .order_by("date")
    )
    return [(row["date"], row["total"]) for row in rows]