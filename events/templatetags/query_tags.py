from django import template
from django.http import QueryDict
from django.urls import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """
    Собирает query string, сохраняя текущие GET-параметры
    и заменяя/удаляя указанные.

    На страницах, отличных от главной, ссылка ведёт на главную
    (чтобы фильтры с детальной события работали корректно).
    """
    request = context['request']
    current = request.GET.copy()

    # На не-главной — ведём на главную с фильтрами
    url_name = request.resolver_match.url_name if request.resolver_match else None
    if url_name != 'home':
        base = reverse('events:home')
    else:
        base = ''

    for key, value in kwargs.items():
        if value == '' or value is None:
            current.pop(key, None)
        else:
            current[key] = value

    # Убираем page при смене фильтра
    current.pop('page', None)

    qs = current.urlencode()
    if qs:
        return f'{base}?{qs}'
    return base or '?'