"""
Теги для работы с SVG-заглушками.

{% random_placeholder %} — возвращает путь к случайной заглушке.

Если нужен детерминированный выбор (например, один и тот же плейсхолдер
для одного и того же объекта), используй:
    {% random_placeholder object.pk %}
    {% random_placeholder event.pk %}
"""
import random

from django import template
from django.templatetags.static import static

register = template.Library()

PLACEHOLDER_COUNT = 50


def _placeholder_path(idx):
    """Путь к SVG по номеру (1..50)."""
    n = ((idx - 1) % PLACEHOLDER_COUNT) + 1
    return static(f'images/placeholders/placeholder-{n:02d}.svg')


@register.simple_tag
def random_placeholder(seed=None):
    """
    Возвращает путь к случайной SVG-заглушке.

    Без аргумента — random каждый раз.
    С аргументом (например, pk) — детерминированно: один и тот же
    объект всегда получает одну и ту же заглушку.
    """
    if seed is None:
        idx = random.randint(1, PLACEHOLDER_COUNT)
    else:
        # стабильный «хэш» от seed
        idx = (hash(str(seed)) % PLACEHOLDER_COUNT) + 1
    return _placeholder_path(idx)