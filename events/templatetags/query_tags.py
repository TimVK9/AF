from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """
    Формирует querystring из текущего request.GET,
    заменяя/удаляя указанные параметры.

    Использование:
        {% querystring category=category.slug %}
        {% querystring date_filter='today' %}
        {% querystring search='' %}   -> удалит search
    """
    request = context.get('request')
    if request is None:
        return ''

    params = request.GET.copy()

    # Сбрасываем page, если не передан явно
    if 'page' not in kwargs:
        params.pop('page', None)

    for key, value in kwargs.items():
        if value is None or value == '':
            params.pop(key, None)
        else:
            params[key] = value

    encoded = params.urlencode()
    return f'?{encoded}' if encoded else '?'