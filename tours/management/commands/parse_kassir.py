"""Парсер мероприятий с nsk.kassir.ru → events.Event."""
import logging
import re
from datetime import datetime, time
from decimal import Decimal, InvalidOperation

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from events.models import Event, Place

logger = logging.getLogger(__name__)

KASSIR_BASE = 'https://nsk.kassir.ru'
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'ru-RU,ru;q=0.9',
}

MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}

VENUE_MAP = {
    'dk-molodost': 'dk-molodost-iskitim',
}


# ======================================================================
#  СЕТЬ
# ======================================================================

def fetch_page(url):
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            return resp.text
        except requests.RequestException as e:
            logger.warning('Попытка %d для %s: %s', attempt + 1, url, e)
    return None


def download_image(url):
    """Скачивает картинку, возвращает ContentFile с именем или None."""
    if not url:
        return None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        content_type = resp.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            return None

        ext = content_type.split('/')[-1].split(';')[0].strip()
        if ext == 'jpeg':
            ext = 'jpg'
        if ext not in ('jpg', 'png', 'gif', 'webp', 'svg'):
            ext = 'jpg'

        filename = url.rstrip('/').split('/')[-1].split('?')[0]
        if not filename or '.' not in filename:
            filename = f'kassir_image.{ext}'
        elif not filename.endswith(f'.{ext}'):
            filename = f'{filename}.{ext}'

        return ContentFile(resp.content, name=filename)
    except Exception as e:
        logger.warning('Не удалось скачать картинку %s: %s', url, e)
        return None


# ======================================================================
#  ПАРСИНГ
# ======================================================================

def parse_price(text):
    """Извлекает минимальную цену из текста."""
    if not text:
        return None
    text = text.replace('\xa0', ' ').replace('\u2009', ' ')
    numbers = re.findall(r'[\d][\d\s]*\d|\d', text)
    prices = []
    for n in numbers:
        n = n.replace(' ', '')
        try:
            prices.append(Decimal(n))
        except (InvalidOperation, ValueError):
            pass
    if not prices:
        if 'бесплатн' in text.lower():
            return Decimal('0')
        return None
    return min(prices)


def parse_age(text):
    if not text:
        return '16+'
    match = re.search(r'(\d+)\+', text)
    if match:
        age = match.group(1)
        valid = ['0', '6', '12', '16', '18']
        return f'{age}+' if age in valid else '16+'
    return '16+'


def parse_date(date_str):
    if not date_str:
        return None
    match = re.match(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_str.strip())
    if match:
        day = int(match.group(1))
        month_name = match.group(2).lower()
        year = int(match.group(3))
        month = MONTHS.get(month_name)
        if month:
            return datetime(year, month, day).date()
    return None


def parse_time_val(time_str):
    if not time_str:
        return None
    match = re.search(r'(\d{1,2}):(\d{2})', time_str)
    if match:
        return time(int(match.group(1)), int(match.group(2)))
    return None


def parse_venue_page(venue_slug):
    """Парсит список событий со страницы площадки."""
    url = f'{KASSIR_BASE}/doma-kultury/{venue_slug}'
    html = fetch_page(url)
    if not html:
        return []

    soup = BeautifulSoup(html, 'lxml')
    events = []
    seen = set()

    for a in soup.find_all('a', href=True):
        href = a['href']
        if venue_slug not in href:
            continue
        if href.startswith('//'):
            event_url = f'https:{href}'
        elif href.startswith('http'):
            event_url = href
        elif href.startswith('/'):
            event_url = f'{KASSIR_BASE}{href}'
        else:
            continue
        parts = event_url.rstrip('/').split(f'/{venue_slug}/')
        if len(parts) < 2 or not parts[1]:
            continue
        external_id = parts[1]
        if external_id not in seen:
            seen.add(external_id)
            events.append({
                'external_id': external_id,
                'kassir_url': event_url,
            })
    return events


def extract_description(soup, full_text):
    """
    Извлекает описание события тремя способами:
      1. Из div с классом, содержащим «description»;
      2. Из текста страницы — между маркерами начала и конца;
      3. Из meta description с очисткой SEO-мусора.
    """
    description = ''

    # --- Способ 1: div с классом description ---
    desc_container = soup.find(
        'div', class_=re.compile(r'description|event-desc|detail-desc', re.I)
    )
    if desc_container:
        description = desc_container.get_text(' ', strip=True)

    # --- Способ 2: вырезаем кусок из текста страницы ---
    if not description or len(description) < 50:
        text = full_text
        start_markers = ['Билеты от', 'Шоу ·', 'Концерт ·', 'Театр ·', '· ']
        end_markers = [
            'Развернуть описание',
            'Организатор:',
            'Место проведения',
            'Свернуть описание',
        ]

        start_pos = -1
        for marker in start_markers:
            pos = text.find(marker)
            if pos != -1:
                start_pos = pos + len(marker)
                break

        end_pos = len(text)
        for marker in end_markers:
            pos = text.find(marker, start_pos if start_pos > 0 else 0)
            if pos != -1 and pos < end_pos:
                end_pos = pos

        if start_pos > 0 and end_pos > start_pos:
            candidate = text[start_pos:end_pos].strip()
            candidate = re.sub(r'^[\s·\-—]+', '', candidate)
            if len(candidate) >= 50:
                description = candidate

    # --- Способ 3: meta description с очисткой ---
    if not description or len(description) < 50:
        desc_tag = soup.find('meta', {'name': 'description'})
        if desc_tag:
            raw = desc_tag.get('content', '')
            raw = re.split(
                r'\s[-–—]\s*(?:в Новосибирске|NSK\.KASSIR|Заказать|Крупнейший)',
                raw, flags=re.I,
            )[0]
            raw = re.sub(r'(?:в Новосибирске|NSK\.KASSIR\.RU).*$', '', raw, flags=re.I)
            raw = re.sub(r'😋.*$', '', raw)
            description = raw.strip()

    return description


def parse_event_detail(event_url):
    """Парсит детальную страницу события."""
    html = fetch_page(event_url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'lxml')

    title_tag = soup.find('h1')
    title = title_tag.get_text(strip=True) if title_tag else None
    if not title:
        return None

    full_text = soup.get_text(' ', strip=True)

    # Дата
    date_str = None
    date_match = re.search(
        r'(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|'
        r'июля|августа|сентября|октября|ноября|декабря)\s+\d{4})',
        full_text, re.IGNORECASE,
    )
    if date_match:
        date_str = date_match.group(1)

    # Время
    time_str = None
    time_match = re.search(r'(\d{1,2}):(\d{2})', full_text)
    if time_match:
        time_str = time_match.group(0)

    # Цена
    price_text = ''
    for tag in soup.find_all(string=re.compile(r'[\d\s]+₽')):
        text = tag.strip()
        if text and ('от' in text.lower() or '—' in text or re.search(r'\d', text)):
            price_text = text
            break

    # Возрастное ограничение
    age_text = None
    age_tag = soup.find(string=re.compile(r'\b\d+\+'))
    if age_tag:
        age_text = age_tag.strip()

    # Картинка
    image_url = ''
    og_image = soup.find('meta', property='og:image')
    if og_image:
        image_url = og_image.get('content', '')

    # Описание
    description = extract_description(soup, full_text)

    return {
        'title': title,
        'date_str': date_str,
        'time_str': time_str,
        'price_text': price_text,
        'age_text': age_text,
        'image_url': image_url,
        'description': description,
    }


# ======================================================================
#  УТИЛИТЫ
# ======================================================================

def make_unique_slug(title, exclude_pk=None):
    base = slugify(title)[:190] or 'event'
    slug = f'kassir-{base}'
    while (
        Event.all_objects
        .filter(slug=slug)
        .exclude(pk=exclude_pk)
        .exists()
    ):
        slug = f'kassir-{base}-{get_random_string(4).lower()}'
    return slug


# ======================================================================
#  КОМАНДА
# ======================================================================

class Command(BaseCommand):
    help = 'Парсит мероприятия с nsk.kassir.ru в events.Event'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Только показать, не сохранять',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        # --- Загружаем площадки из БД ---
        places = {}
        for kassir_slug, place_slug in VENUE_MAP.items():
            place = Place.objects.filter(slug=place_slug).first()
            if place:
                places[kassir_slug] = place
            else:
                self.stdout.write(self.style.WARNING(
                    f'Площадка {place_slug} не найдена в БД. '
                    f'Создайте её через админку.'
                ))

        if not places:
            self.stdout.write(self.style.ERROR('Нет площадок для парсинга.'))
            return

        # --- Парсим список событий со всех площадок ---
        all_events = []
        for kassir_slug, place in places.items():
            self.stdout.write(f'Парсинг: {kassir_slug} → {place.name}')
            events = parse_venue_page(kassir_slug)
            for ev in events:
                ev['place'] = place
            all_events.extend(events)
            self.stdout.write(f'  Найдено: {len(events)}')

        self.stdout.write(f'\nВсего событий: {len(all_events)}')

        if dry_run:
            for ev in all_events:
                self.stdout.write(f'  [{ev["external_id"]}] {ev["kassir_url"]}')
            return

        # --- Сохраняем в БД ---
        created = 0
        updated = 0
        skipped = 0
        active_external_ids = set()

        for ev in all_events:
            active_external_ids.add(ev['external_id'])

            # Парсим детальную страницу
            detail = parse_event_detail(ev['kassir_url'])
            if not detail:
                skipped += 1
                self.stdout.write(self.style.WARNING(
                    f'  ? Не удалось распарсить: {ev["kassir_url"]}'
                ))
                continue

            start_date = parse_date(detail.get('date_str'))
            if not start_date:
                skipped += 1
                self.stdout.write(self.style.WARNING(
                    f'  ? Нет даты: {detail["title"]}'
                ))
                continue

            start_time = parse_time_val(detail.get('time_str'))
            price = parse_price(detail.get('price_text'))
            age = parse_age(detail.get('age_text'))

            desc = detail.get('description', '')
            desc_short = desc[:500] if desc else ''

            # Ищем существующее событие по external_id
            existing = (
                Event.all_objects
                .filter(external_id=ev['external_id'])
                .exclude(external_id='')
                .first()
            )

            if existing:
                # --- Обновляем существующее ---
                existing.title = detail['title']
                existing.external_url = ev['kassir_url']
                existing.status = Event.Status.PUBLISHED
                existing.is_deleted = False
                existing.start_date = start_date

                if start_time is not None:
                    existing.start_time = start_time

                if price is not None:
                    existing.price = price

                existing.age_restriction = age

                if desc:
                    existing.description = desc
                    existing.description_short = desc_short

                # Картинку обновляем только если её не было
                if not existing.main_image and detail.get('image_url'):
                    image_file = download_image(detail['image_url'])
                    if image_file:
                        existing.main_image = image_file

                existing.save()
                updated += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  ~ {existing.title} ({start_date})'
                ))

            else:
                # --- Создаём новое ---
                slug = make_unique_slug(detail['title'])

                image_file = None
                if detail.get('image_url'):
                    image_file = download_image(detail['image_url'])

                Event.all_objects.create(
                    title=detail['title'],
                    slug=slug,
                    description_short=desc_short or 'Подробнее на kassir.ru',
                    description=desc or desc_short or 'Подробнее на kassir.ru',
                    status=Event.Status.PUBLISHED,
                    place=ev['place'],
                    category=None,
                    start_date=start_date,
                    start_time=start_time,
                    price=price,
                    age_restriction=age,
                    external_id=ev['external_id'],
                    external_url=ev['kassir_url'],
                    main_image=image_file,
                )
                created += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  + {detail["title"]} ({start_date})'
                ))

        # --- Деактивируем пропавшие события ---
        if active_external_ids:
            deactivated = (
                Event.all_objects
                .filter(external_id__isnull=False)
                .exclude(external_id='')
                .exclude(external_id__in=active_external_ids)
                .update(status=Event.Status.DRAFT)
            )
        else:
            deactivated = 0

        self.stdout.write('\n--- Итог ---')
        self.stdout.write(f'Создано: {created}')
        self.stdout.write(f'Обновлено: {updated}')
        self.stdout.write(f'Пропущено: {skipped}')
        if deactivated:
            self.stdout.write(f'Снято в черновики: {deactivated}')
