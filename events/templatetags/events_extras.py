from django import template
from urllib.parse import urlparse

register = template.Library()


@register.filter
def domain(url):
    """Извлекает домен из URL: https://nsk.kassir.ru/event/123 → nsk.kassir.ru"""
    if not url:
        return ''
    parsed = urlparse(url)
    return parsed.netloc or url
