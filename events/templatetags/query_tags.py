"""
Теги для работы с GET-параметрами в шаблонах.

Использование:
    {% load query_tags %}
    <a href="{% querystring category='' %}">Все</a>
    <a href="{% querystring page=2 %}">Стр. 2</a>
"""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """
    Возвращает строку GET-параметров, где переданные kwargs
    заменяют или удаляют соответствующие ключи.

    Пустое значение ('' или None) — удаляет ключ.
    Если 'page' не передан явно — сбрасывает пагинацию.
    """
    request = context.get('request')
    if request is None:
        return ''

    query = request.GET.copy()

    for key, value in kwargs.items():
        if value in (None, ''):
            query.pop(key, None)
        else:
            query[key] = value

    if 'page' not in kwargs:
        query.pop('page', None)

    encoded = query.urlencode()
    return f'?{encoded}' if encoded else ''