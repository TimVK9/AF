"""
RSS-фиды для афиши.

Маршруты:
    /rss/                        — все опубликованные события
    /rss/category/<slug>/        — события одной категории
    /rss/place/<slug>/           — события одной площадки

Фид отдаёт полное описание (content:encoded), категории,
обложку (enclosure), даты события и место. Это даёт Google
и Яндексу достаточно контента для быстрой индексации.
"""
from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.feedgenerator import Rss201rev2Feed

from .models import Event, Category, Place


# ---------------------------------------------------------
#  Кастомный генератор: добавляет namespace event:
# ---------------------------------------------------------
class EventAwareFeedGenerator(Rss201rev2Feed):
    """
    Добавляет в <rss> namespace для собственных тегов:
    event:startDate, event:endDate, event:location, event:price.
    """

    def rss_attributes(self):
        attrs = super().rss_attributes()
        attrs['xmlns:content'] = 'http://purl.org/rss/1.0/modules/content/'
        attrs['xmlns:dc'] = 'http://purl.org/dc/elements/1.1/'
        attrs['xmlns:atom'] = 'http://www.w3.org/2005/Atom'
        attrs['xmlns:event'] = 'https://schema.org/Event'
        return attrs

    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)

        if item.get('event_start'):
            handler.addQuickElement('event:startDate', item['event_start'])
        if item.get('event_end'):
            handler.addQuickElement('event:endDate', item['event_end'])
        if item.get('event_location'):
            handler.addQuickElement('event:location', item['event_location'])
        if item.get('event_price'):
            handler.addQuickElement('event:price', item['event_price'])
        if item.get('event_free'):
            handler.addQuickElement('event:isAccessibleForFree', 'true')


# ---------------------------------------------------------
#  Базовый класс — общая логика для всех трёх фидов
# ---------------------------------------------------------
class BaseEventsFeed(Feed):
    feed_type = EventAwareFeedGenerator
    feed_copyright = '© Афиша Искитим'
    ttl = 60  # минуты: как часто читалкам перезапрашивать фид

    # -----------------------------------------------------
    #  Общие элементы <channel>
    # -----------------------------------------------------
    def feed_extra_kwargs(self, obj):
        """Дополнительные параметры в <rss>."""
        return {}

    def link(self, obj):
        # Абсолютный URL главной
        return reverse('events:home')

    def feed_description(self, obj):
        return (
            'События Искитима: концерты, спектакли, выставки, '
            'фестивали и другие мероприятия города.'
        )

    def feed_copyright_text(self):
        year = timezone.localdate().year
        return f'© {year} Афиша Искитим'

    # -----------------------------------------------------
    #  Кэширование: 15 минут — краулеры не душат БД
    # -----------------------------------------------------
    def get_object(self, request, *args, **kwargs):
        # Возвращаем запрос, чтобы не дёргать БД в items()
        return None

    # -----------------------------------------------------
    #  Базовый queryset
    # -----------------------------------------------------
    def base_queryset(self):
        today = timezone.localdate()

        # Будущие события + недавно прошедшие (за 60 дней).
        # Отдаём и те и другие — Google узнаёт и о новом,
        # и о том, что событие «завершилось».
        horizon_past = today - timezone.timedelta(days=60)

        return (
            Event.objects
            .filter(status=Event.Status.PUBLISHED)
            .filter(
                Q(start_date__gte=horizon_past)
            )
            .select_related('category', 'place')
        )

    # -----------------------------------------------------
    #  Заголовок канала — переопределяется в наследниках
    # -----------------------------------------------------
    def title(self, obj):
        return 'Афиша Искитим — новые события'

    # -----------------------------------------------------
    #  Элементы — по одному на событие
    # -----------------------------------------------------
    def items(self, obj):
        # obj может быть Category / Place — переопределяем
        # через self._filter_qs(obj)
        qs = self._filter_qs(obj)
        return qs.order_by('-created_at')[:100]

    def _filter_qs(self, obj):
        """Переопределяется в наследниках."""
        return self.base_queryset()

    # -----------------------------------------------------
    #  Описание элемента
    # -----------------------------------------------------
    def item_title(self, item):
        return item.title

    def item_description(self, item):
        """
        Краткое описание + структурированный блок с фактами.
        Используется читалками, у которых нет content:encoded.
        """
        parts = []

        if item.description_short:
            parts.append(f'<p>{item.description_short}</p>')

        parts.append('<ul>')

        # Дата
        if item.end_date and item.end_date != item.start_date:
            parts.append(
                f'<li><strong>Дата:</strong> '
                f'{item.start_date:%d.%m.%Y} — {item.end_date:%d.%m.%Y}</li>'
            )
        else:
            parts.append(
                f'<li><strong>Дата:</strong> {item.start_date:%d.%m.%Y}</li>'
            )

        # Время
        if item.start_time:
            time_str = f'{item.start_time:%H:%M}'
            if item.end_time:
                time_str += f' — {item.end_time:%H:%M}'
            parts.append(f'<li><strong>Время:</strong> {time_str}</li>')

        # Место
        if item.place:
            place_str = item.place.name
            if item.place.short_address:
                place_str += f', {item.place.short_address}'
            parts.append(f'<li><strong>Место:</strong> {place_str}</li>')

        # Цена
        if item.is_free:
            parts.append('<li><strong>Вход:</strong> свободный</li>')
        elif item.price:
            parts.append(f'<li><strong>Цена:</strong> {item.price} ₽</li>')
        else:
            parts.append('<li><strong>Цена:</strong> уточняется</li>')

        # Возраст
        parts.append(
            f'<li><strong>Возраст:</strong> {item.age_restriction}</li>'
        )

        parts.append('</ul>')

        return ''.join(parts)

    def item_link(self, item):
        return reverse('events:event_detail', args=[item.slug])

    def item_pubdate(self, item):
        return item.created_at

    def item_updateddate(self, item):
        return item.updated_at

    # -----------------------------------------------------
    #  Полное описание (content:encoded)
    # -----------------------------------------------------
    def item_extra_kwargs(self, item):
        # --- content:encoded: полный текст описания ---
        content_parts = []
        if item.description_short:
            content_parts.append(f'<p><strong>{item.description_short}</strong></p>')

        if item.description:
            # linebreaks превращает \n\n в <p>, одиночный \n — в <br>
            content_parts.append(item.description.replace('\n\n', '</p><p>').replace('\n', '<br>'))
            # обернуть в <p>…</p>, если ещё нет
            html = ''.join(content_parts)
            if '<p>' not in html:
                html = f'<p>{html}</p>'
        else:
            html = ''.join(content_parts)

        # --- enclosure: главное изображение ---
        enclosure_url = None
        enclosure_length = 0
        enclosure_type = 'image/jpeg'

        image_field = item.main_image or (item.place.main_image if item.place else None)
        if image_field:
            try:
                enclosure_url = image_field.url
                enclosure_length = image_field.size or 0
            except (ValueError, OSError):
                enclosure_url = None

        # --- item-level extra ---
        extra = {
            'content_encoded': html,
            'event_start': (
                f'{item.start_date.isoformat()}'
                + (f'T{item.start_time.isoformat()}' if item.start_time else '')
            ),
            'event_end': (
                (item.end_date or item.start_date).isoformat()
                + (f'T{item.end_time.isoformat()}' if item.end_time else '')
            ),
            'event_location': (
                f'{item.place.name}, {item.place.short_address}'
                if item.place else ''
            ),
            'event_price': str(item.price) if item.price is not None else '',
            'event_free': item.is_free,
        }

        if enclosure_url:
            extra['enclosure'] = {
                'url': enclosure_url,
                'length': enclosure_length,
                'mime_type': enclosure_type,
            }

        return extra

    # -----------------------------------------------------
    #  Категории элемента
    # -----------------------------------------------------
    def item_categories(self, item):
        cats = []
        if item.category:
            cats.append(item.category.name)
        if item.place:
            cats.append(item.place.name)
        return cats

    # -----------------------------------------------------
    #  Автор элемента
    # -----------------------------------------------------
    def item_author_name(self, item):
        return item.organizer_name or 'Афиша Искитим'

    def item_author_link(self, item):
        if item.organizer_vk:
            return item.organizer_vk
        return None


# ---------------------------------------------------------
#  Фид 1: все события
# ---------------------------------------------------------
class LatestEventsFeed(BaseEventsFeed):
    """Общий фид — все опубликованные события."""

    def title(self, obj):
        return 'Афиша Искитим — новые события'

    def description(self, obj):
        return (
            'Все опубликованные события Искитима: концерты, '
            'спектакли, выставки, фестивали.'
        )

    def _filter_qs(self, obj):
        return self.base_queryset()


# ---------------------------------------------------------
#  Фид 2: события одной категории
# ---------------------------------------------------------
class CategoryEventsFeed(BaseEventsFeed):
    """Фид событий одной категории. URL: /rss/category/<slug>/"""

    def get_object(self, request, slug):
        return Category.objects.filter(slug=slug, is_active=True).first()

    def title(self, obj):
        if obj is None:
            return 'Афиша Искитим — события категории'
        return f'Афиша Искитим — {obj.name}'

    def description(self, obj):
        if obj is None:
            return 'События Искитима'
        if obj.description:
            return obj.description
        return f'События категории «{obj.name}» в Искитиме.'

    def link(self, obj):
        if obj is None:
            return reverse('events:home')
        return f"{reverse('events:home')}?category={obj.slug}"

    def _filter_qs(self, obj):
        qs = self.base_queryset()
        if obj is not None:
            qs = qs.filter(category=obj)
        return qs


# ---------------------------------------------------------
#  Фид 3: события одной площадки
# ---------------------------------------------------------
class PlaceEventsFeed(BaseEventsFeed):
    """Фид событий одной площадки. URL: /rss/place/<slug>/"""

    def get_object(self, request, slug):
        return Place.objects.filter(slug=slug).first()

    def title(self, obj):
        if obj is None:
            return 'Афиша Искитим — события площадки'
        return f'Афиша Искитим — {obj.name}'

    def description(self, obj):
        if obj is None:
            return 'События Искитима'
        if obj.description:
            return obj.description
        return f'События площадки «{obj.name}» в Искитиме.'

    def link(self, obj):
        if obj is None:
            return reverse('events:home')
        return reverse('events:place_detail', args=[obj.slug])

    def _filter_qs(self, obj):
        qs = self.base_queryset()
        if obj is not None:
            qs = qs.filter(place=obj)
        return qs