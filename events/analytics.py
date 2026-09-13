"""
Обезличенная внутренняя статистика.

Принцип:
  • инкремент счётчика через атомарный UPSERT;
  • никаких ПДн — ни IP, ни cookies, ни User-Agent, ни session_id;
  • храним только агрегаты: «сколько раз за день посмотрели объект X».

object_id = 0 означает «не применимо» (главная страница, поиск).
Это сделано потому, что в SQL NULL != NULL, и unique-констрейнт
с NULL не работал бы — можно было бы создать сколько угодно дублей
за один день для главной и поиска.
"""

from django.db import models
from django.db.models import F
from django.utils import timezone

from .models.models_analytics import PageView


# ======================================================================
#  Инкремент счётчика
# ======================================================================

def track_view(kind: str, object_id: int = 0) -> None:
    """
    Увеличивает счётчик просмотров на 1 для пары (kind, object_id)
    на сегодняшнюю дату.

    kind: "event" | "place" | "category" | "home" | "search"
    object_id: ID объекта; 0 — для главной и поиска.

    Логика:
      1. Атомарно инкрементируем существующую строку.
         UPDATE ... WHERE kind=... AND object_id=... AND date=...
         возвращает число изменённых строк — если 0, значит записи нет.
      2. Если строки нет — пытаемся вставить.
         `ignore_conflicts=True` превращается в INSERT ... ON CONFLICT
         DO NOTHING (PostgreSQL) или INSERT OR IGNORE (SQLite).
         Если параллельный запрос успел вставить ту же строку —
         вставка молча пропускается, и мы идём на шаг 3.
      3. Если вставка не состоялась — значит, запись уже создана кем-то
         другим, инкрементим её.

    Никаких try/except: конфликт уникальности обрабатывается на уровне
    БД, а не через исключения, поэтому транзакция не ломается.
    """
    today = timezone.localdate()

    # Шаг 1: атомарный инкремент существующей записи.
    updated = PageView.objects.filter(
        kind=kind,
        object_id=object_id,
        date=today,
    ).update(count=F("count") + 1)

    if updated:
        return

    # Шаг 2: записи нет — пытаемся создать.
    # bulk_create возвращает список реально вставленных объектов.
    # При ignore_conflicts=True конфликтующие строки в него не попадут.
    created = PageView.objects.bulk_create(
        [PageView(kind=kind, object_id=object_id, date=today, count=1)],
        ignore_conflicts=True,
    )

    # Шаг 3: если вставка не прошла — запись уже есть, инкрементим её.
    if not created:
        PageView.objects.filter(
            kind=kind,
            object_id=object_id,
            date=today,
        ).update(count=F("count") + 1)


# ======================================================================
#  Аналитика: топы и дневные сводки
# ======================================================================

def get_top(kind: str, days: int = 7, limit: int = 10):
    """
    Топ-N объектов за последние `days` дней (сумма счётчиков по дням).

    Возвращает QuerySet словарей вида:
        {"object_id": <id>, "total": <сумма просмотров>}

    object_id=0 (главная, поиск) исключается — у них нет «объекта».
    """
    since = timezone.localdate() - timezone.timedelta(days=days)

    return (
        PageView.objects
        .filter(
            kind=kind,
            date__gte=since,
            object_id__gt=0,   # исключаем «не применимо»
        )
        .values("object_id")
        .annotate(total=models.Sum("count"))
        .order_by("-total")[:limit]
    )


def get_daily_stats(kind: str, days: int = 30):
    """
    Список (дата, сумма просмотров) за последние `days` дней.

    Возвращает список кортежей:
        [(date(2026, 9, 1), 123), (date(2026, 9, 2), 145), ...]

    object_id не учитывается — суммируем всё по kind.
    Для главной и поиска это даст корректный дневной график.
    """
    since = timezone.localdate() - timezone.timedelta(days=days)

    rows = (
        PageView.objects
        .filter(kind=kind, date__gte=since)
        .values("date")
        .annotate(total=models.Sum("count"))
        .order_by("date")
    )
    return [(row["date"], row["total"]) for row in rows]


# ======================================================================
#  Дополнительные хелперы (по желанию)
# ======================================================================

def get_object_total(kind: str, object_id: int, days: int = 30) -> int:
    """
    Суммарное число просмотров конкретного объекта за `days` дней.
    Возвращает int (0, если записей нет).
    """
    since = timezone.localdate() - timezone.timedelta(days=days)

    result = (
        PageView.objects
        .filter(kind=kind, object_id=object_id, date__gte=since)
        .aggregate(total=models.Sum("count"))
    )
    return result["total"] or 0


def get_stats_range(kind: str, date_from, date_to):
    """
    Просмотры по дням в произвольном диапазоне [date_from; date_to].
    Полезно для отчётов и графиков за конкретный период.
    """
    rows = (
        PageView.objects
        .filter(kind=kind, date__gte=date_from, date__lte=date_to)
        .values("date")
        .annotate(total=models.Sum("count"))
        .order_by("date")
    )
    return [(row["date"], row["total"]) for row in rows]