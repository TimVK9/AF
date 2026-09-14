"""
Тег для генерации стабильной SVG-заглушки.

Использование:
    {% load placeholders %}
    <img src="{% random_placeholder event.pk %}">
"""
from urllib.parse import quote

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


# Палитры для плейсхолдеров: (тёмный, светлый)
PALETTES = [
    ('#0f766e', '#5eead4'),  # изумрудный
    ('#1e40af', '#93c5fd'),  # синий
    ('#7c3aed', '#c4b5fd'),  # фиолетовый
    ('#b45309', '#fcd34d'),  # янтарный
    ('#9f1239', '#fda4af'),  # малиновый
]


def _seed_to_index(seed, modulo):
    """Стабильный индекс из seed."""
    try:
        n = int(seed)
    except (TypeError, ValueError):
        n = sum(ord(c) for c in str(seed or ''))
    return n % modulo


@register.simple_tag
def random_placeholder(seed):
    """
    Возвращает data-URI с SVG-заглушкой.
    Для одного и того же seed результат всегда одинаков.
    """
    dark, light = PALETTES[_seed_to_index(seed, len(PALETTES))]

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="0 0 1200 675" preserveAspectRatio="xMidYMid slice">'
        '<defs>'
        '<linearGradient id="g" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{dark}"/>'
        f'<stop offset="100%" stop-color="{light}"/>'
        '</linearGradient>'
        '</defs>'
        '<rect width="1200" height="675" fill="url(#g)"/>'
        '<circle cx="960" cy="140" r="70" fill="#ffffff" opacity="0.15"/>'
        '<circle cx="200" cy="500" r="120" fill="#ffffff" opacity="0.08"/>'
        '</svg>'
    )

    encoded = quote(svg, safe='')
    return mark_safe(f"data:image/svg+xml;charset=utf-8,{encoded}")