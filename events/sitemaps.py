"""
Карты сайта для поисковых систем.

Используется штатный фреймворк django.contrib.sitemaps.
- EventSitemap — все опубликованные события
- StaticViewSitemap — статические страницы (главная, о нас, контакты...)
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from events.models.event import Event



class EventSitemap(Sitemap):
    """Все опубликованные события."""
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return (
            Event.objects
            .filter(status=Event.Status.PUBLISHED)
            .order_by('-updated_at')
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('events:event_detail', kwargs={'slug': obj.slug})


class StaticViewSitemap(Sitemap):
    """Статические страницы."""
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return [
            'events:home',
            'pages:about',
            'pages:contacts',
            'pages:help',
            'pages:privacy',
            'pages:cookies',
            'pages:terms',
        ]

    def location(self, item):
        return reverse(item)