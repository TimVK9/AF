from django import template

register = template.Library()


@register.filter
def is_portrait(image):
    """Возвращает True, если изображение вертикальное (высота > ширины)."""
    try:
        return image.height > image.width
    except (AttributeError, TypeError):
        return False
