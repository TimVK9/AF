"""
Парсер афиши с kultisk.ru/afisha/.

Страница — обычный WordPress, мероприятия лежат в HTML-таблицах.
Команда скачивает HTML, разбирает таблицы, создаёт события
в статусе MODERATION для ручной проверки.

Категории НЕ создаются автоматически. Парсер ищет существующую
категорию по фиксированному slug (CATEGORY_SLUGS). Если категории
нет — событие сохраняется БЕЗ категории.

Категории определяются:
  • 2-колоночные таблицы (Выставки) → категория «Выставки»;
  • остальные — по ключевым словам в названии (CATEGORY_RULES).

Площадки создаются автоматически, если не найдены (это безопасно —
они создаются как обычные справочники).

Использование:
    python manage.py parse_kultisk_afisha --dry-run
    python manage.py parse_kultisk_afisha
"""

import re
from datetime import date, time as dt_time, timedelta

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from events.models import Event, Category, Place


URL = 'https://kultisk.ru/afisha/'
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0 Safari/537.36'
    ),
}

# Площадка по умолчанию для выставок (2-колоночные таблицы без места)
DEFAULT_EXHIBITION_PLACE = 'Искитимский городской историко-художественный музей'

# Категория по умолчанию, если ничего не совпало
DEFAULT_CATEGORY = 'Прочее'

# Алиасы названий площадок: как на сайте → как у нас в БД.
PLACE_ALIASES = {
    'кцсон': 'Комплексный центр социального обслуживания населения',
    'д/с медвежонок': 'Детский сад «Медвежонок»',
    'цбс': 'Централизованная библиотечная система',
    'дк молодость': 'ДК «Молодость»',
    'дк октябрь': 'ДК «Октябрь»',
    'дк россия': 'ДК «Россия»',
    'иг ихм': 'Искитимский городской историко-художественный музей',
    'искитимский городской историко-художественный музей': (
        'Искитимский городской историко-художественный музей'
    ),
}

# Правила автоопределения категории по названию.
# Порядок ВАЖЕН: первое совпадение выигрывает.
CATEGORY_RULES = [
    ('Концерты', [
        'концерт', 'ансамбль', 'хор', 'филармония', 'вокальный',
        'музыкальн', 'симфонич', 'оркестр',
    ]),
    ('Спектакли', [
        'спектакль', 'театр', 'мюзикл', 'кукольн', 'драматич',
        'постановка',
    ]),
    ('Выставки', [
        'выставк', 'экспозиц', 'вернисаж', 'картин', 'график',
        'живопис', 'фотовыставк',
    ]),
    ('Мастер-классы', [
        'мастер-класс', 'мастер класс', 'кружок', 'школа',
        'творческая мастерская', 'скрапбукинг',
    ]),
    ('Кино', [
        'кинопоказ', 'кино', 'фильм', 'видеокруиз', 'мультфильм',
    ]),
    ('Экскурсии', [
        'экскурс', 'пешая', 'музейный проект',
    ]),
    ('Акции', [
        'акци', 'субботник', 'волонтёр', 'волонтер', 'капля жизни',
        'эко-вызов',
    ]),
    ('Праздники', [
        'праздник', 'фестивал', 'открытие сезона', 'новый год',
        'курбан', 'масленица', 'день города',
    ]),
    ('Игры и квесты', [
        'квиз', 'квест', 'викторина', 'игра', 'игровая', 'турнир',
    ]),
    ('Встречи', [
        'встреча', 'гостиная', 'клуб', 'диалог', 'час памяти',
    ]),
]

# Фиксированные slug'и для категорий.
# Парсер только ИЩЕТ категории по этим slug. Если категории нет —
# событие сохраняется БЕЗ категории (не создаётся автоматически).
CATEGORY_SLUGS = {
    'Концерты': 'concerts',
    'Спектакли': 'theatre',
    'Выставки': 'exhibitions',
    'Мастер-классы': 'workshops',
    'Кино': 'cinema',
    'Экскурсии': 'excursions',
    'Акции': 'actions',
    'Праздники': 'holidays',
    'Игры и квесты': 'games',
    'Встречи': 'meetings',
    'Прочее': 'other',
}


def detect_category(title, default=DEFAULT_CATEGORY):
    """Определяет категорию по ключевым словам в названии."""
    text = (title or '').lower()
    for category_name, keywords in CATEGORY_RULES:
        for kw in keywords:
            if kw in text:
                return category_name
    return default


class Command(BaseCommand):
    help = (
        'Парсит афишу с kultisk.ru/afisha/ и создаёт события '
        'в статусе MODERATION. Категории определяются автоматически, '
        'но новые НЕ создаются.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Не сохранять в БД, только показать, что было бы создано',
        )

    # ------------------------------------------------------------------ #
    #  Точка входа                                                       #
    # ------------------------------------------------------------------ #

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']

        self.skipped_no_date = []
        self.seen_keys = set()
        self.missing_categories = set()

        self.stdout.write(f'Скачиваю {URL} ...')
        html = self._fetch()
        self.stdout.write(self.style.SUCCESS(f'OK, {len(html)} байт\n'))

        soup = BeautifulSoup(html, 'lxml')
        tables = self._extract_tables(soup)
        self.stdout.write(f'Найдено таблиц: {len(tables)}\n')

        total_created = 0
        total_skipped = 0
        total_parsed = 0
        total_no_category = 0

        for table in tables:
            context = table['context']
            for row in table['rows']:
                parsed = self._parse_row(row, context)
                if not parsed:
                    self.skipped_no_date.append(row)
                    continue

                total_parsed += 1

                # Определяем название категории
                if parsed.get('category_hint'):
                    cat_name = parsed['category_hint']
                else:
                    cat_name = detect_category(parsed['title'])

                # Ищем категорию по slug (без создания)
                category = self._get_category(cat_name)
                if category is None:
                    total_no_category += 1
                    self.missing_categories.add(cat_name)

                if self.dry_run:
                    key = (parsed['title'], parsed['start_date'])
                    if key in self.seen_keys:
                        self.stdout.write(
                            f'[SKIP] дубль: {parsed["title"][:60]}\n'
                        )
                        continue
                    self.seen_keys.add(key)

                    end = parsed.get('end_date')
                    end_str = f' → {end}' if end else ''
                    cat_str = cat_name if category else f'{cat_name} (нет в БД)'
                    self.stdout.write(
                        f'[DRY] [{cat_str}] '
                        f'{parsed["start_date"]}{end_str} | '
                        f'{parsed["title"][:60]} | '
                        f'{parsed["place_name"]}\n'
                    )
                    continue

                created = self._save_event(parsed, category)
                if created:
                    total_created += 1
                else:
                    total_skipped += 1

        self.stdout.write(f'\nРазобрано строк: {total_parsed}\n')
        self.stdout.write(
            f'Пропущено (не распознал дату): {len(self.skipped_no_date)}\n'
        )
        if total_no_category:
            self.stdout.write(
                f'Без категории (не найдена в БД): {total_no_category}\n'
            )

        for row in self.skipped_no_date[:10]:
            self.stdout.write(f'  · {row}\n')

        if self.missing_categories:
            self.stdout.write('\nНе найдены категории (создайте вручную):\n')
            for name in sorted(self.missing_categories):
                slug = CATEGORY_SLUGS.get(name, slugify(name))
                self.stdout.write(f'  ! {name} (slug: {slug})\n')

        if self.dry_run:
            self.stdout.write('\n')
            self.stdout.write(self.style.WARNING(
                'Режим --dry-run: ничего не сохранено.\n'
            ))
        else:
            self.stdout.write('\n')
            self.stdout.write(self.style.SUCCESS(
                f'Создано: {total_created}, '
                f'пропущено (дубли): {total_skipped}\n'
            ))

    # ------------------------------------------------------------------ #
    #  Загрузка и разбор HTML                                            #
    # ------------------------------------------------------------------ #

    def _fetch(self):
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        return resp.text

    def _extract_tables(self, soup):
        """
        Возвращает список словарей:
          {'context': 'plan' | 'exhibitions', 'rows': [ {cells: [...]} ]}
        """
        result = []

        for table in soup.find_all('table'):
            context = self._detect_context(table)

            rows = []
            for tr in table.find_all('tr'):
                cells = [
                    self._clean_text(td.get_text('\n', strip=True))
                    for td in tr.find_all(['td', 'th'])
                ]
                if not cells:
                    continue
                first = cells[0].strip().lower()
                if first in ('дата',):
                    continue
                rows.append(cells)

            if rows:
                result.append({'context': context, 'rows': rows})

        return result

    def _detect_context(self, table):
        """
        Идёт вверх по дереву, ищет <strong>, содержащий
        'План мероприятий' или 'Выставки'.
        """
        prev = table.find_previous(['strong', 'p', 'h2', 'h3'])
        text = self._clean_text(prev.get_text(' ', strip=True)) if prev else ''
        text_lower = text.lower()

        if 'выставк' in text_lower:
            return 'exhibitions'
        if 'план мероприятий' in text_lower:
            return 'plan'
        return 'plan'

    def _clean_text(self, s):
        """Убирает \xa0, лишние пробелы, переносы."""
        if not s:
            return ''
        s = s.replace('\xa0', ' ')
        s = re.sub(r'\n{2,}', '\n', s)
        s = re.sub(r'[ \t]+', ' ', s)
        return s.strip()

    # ------------------------------------------------------------------ #
    #  Разбор одной строки таблицы                                       #
    # ------------------------------------------------------------------ #

    def _parse_row(self, cells, context):
        """
        4 колонки → План мероприятий (дата, время, название, место).
        2 колонки → Выставки (дата, название), место — музей,
        категория — «Выставки».
        """
        try:
            if len(cells) >= 4:
                event = self._build_event(
                    date_raw=cells[0],
                    time_raw=cells[1],
                    title_raw=cells[2],
                    place_raw=cells[3],
                )
                if event:
                    event['category_hint'] = None
                return event

            if len(cells) == 2:
                event = self._build_event(
                    date_raw=cells[0],
                    time_raw='',
                    title_raw=cells[1],
                    place_raw=DEFAULT_EXHIBITION_PLACE,
                )
                if event:
                    event['category_hint'] = 'Выставки'
                return event
        except Exception as exc:
            self.stderr.write(f'Ошибка на строке {cells}: {exc}')
        return None

    def _build_event(self, date_raw, time_raw, title_raw, place_raw):
        title = self._clean_title(title_raw)
        if not title or len(title) < 3:
            return None

        start_date, end_date = self._parse_date_range(date_raw)
        if not start_date:
            return None

        start_time = self._parse_time(time_raw)
        place_name = self._normalize_place(place_raw)

        return {
            'title': title[:200],
            'start_date': start_date,
            'end_date': end_date,
            'start_time': start_time,
            'place_name': place_name[:255],
            'description_short': title[:500],
            'description': f'{title}\n\nИсточник: kultisk.ru',
            'category_hint': None,
        }

    def _clean_title(self, raw):
        """Чистит название: схлопывает пробелы, обрезает длинные."""
        if not raw:
            return ''
        raw = re.sub(r'\s+', ' ', raw).strip()

        if len(raw) > 200:
            idx = raw.rfind('.', 0, 200)
            if idx > 50:
                raw = raw[:idx + 1]
            else:
                raw = raw[:197] + '...'

        return raw

    def _normalize_place(self, raw):
        """Нормализует название площадки: чистит многострочность, применяет алиасы."""
        if not raw:
            return 'Уточняется'

        lines = [l.strip() for l in raw.split('\n') if l.strip()]
        if lines:
            raw = lines[0]

        raw_clean = re.sub(r'\s*\([^)]*\)\s*', ' ', raw).strip()
        raw_clean = raw_clean.rstrip(' ,.;:')

        key = raw_clean.lower()
        for alias, full in PLACE_ALIASES.items():
            if alias in key:
                return full

        return raw_clean or raw

    # ------------------------------------------------------------------ #
    #  Парсинг даты                                                      #
    # ------------------------------------------------------------------ #

    def _parse_date_range(self, raw):
        """
        Разбирает форматы:
          02-10.09.2026          → 02.09.2026 – 10.09.2026
          07.09.2026             → 07.09.2026
          07-10.09.2026          → 07.09.2026 – 10.09.2026
          01.06-17.09.2026       → 01.06.2026 – 17.09.2026
          01.06.2026-17.09.2026  → 01.06.2026 – 17.09.2026
          04.09-31.11.2026       → 04.09.2026 – 30.11.2026 (корректируем)
        Возвращает (start_date, end_date) или (None, None).
        """
        if not raw:
            return None, None

        raw = raw.strip()
        if raw.lower() in ('по договоренности', 'в течение дня', ''):
            return None, None

        # Полный диапазон с двумя годами: 01.06.2026-17.09.2026
        m = re.match(
            r'(\d{2})\.(\d{2})\.(\d{4})\s*[-—]\s*(\d{2})\.(\d{2})\.(\d{4})',
            raw,
        )
        if m:
            d1, mo1, y1, d2, mo2, y2 = map(int, m.groups())
            return self._safe_date(y1, mo1, d1), self._safe_date(y2, mo2, d2)

        # Диапазон ДД-ДД.ММ.ГГГГ: 02-10.09.2026
        m = re.match(r'(\d{1,2})\s*[-—]\s*(\d{1,2})\.(\d{2})\.(\d{4})', raw)
        if m:
            d1, d2, mo, y = map(int, m.groups())
            return self._safe_date(y, mo, d1), self._safe_date(y, mo, d2)

        # Диапазон ДД.ММ-ДД.ММ.ГГГГ: 01.06-17.09.2026
        m = re.match(
            r'(\d{1,2})\.(\d{2})\s*[-—]\s*(\d{1,2})\.(\d{2})\.(\d{4})',
            raw,
        )
        if m:
            d1, mo1, d2, mo2, y = map(int, m.groups())
            return self._safe_date(y, mo1, d1), self._safe_date(y, mo2, d2)

        # Одна дата ДД.ММ.ГГГГ
        m = re.match(r'(\d{1,2})\.(\d{2})\.(\d{4})', raw)
        if m:
            d, mo, y = map(int, m.groups())
            return self._safe_date(y, mo, d), None

        return None, None

    def _safe_date(self, year, month, day):
        """Создаёт date, корректируя невозможные дни (31.11 → 30.11)."""
        try:
            return date(year, month, day)
        except ValueError:
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
            return next_month - timedelta(days=1)

    # ------------------------------------------------------------------ #
    #  Парсинг времени                                                   #
    # ------------------------------------------------------------------ #

    def _parse_time(self, raw):
        """Разбирает '12:00', '18:30'. Возвращает time или None."""
        if not raw:
            return None
        m = re.match(r'(\d{1,2}):(\d{2})', raw.strip())
        if not m:
            return None
        h, mi = int(m.group(1)), int(m.group(2))
        if 0 <= h < 24 and 0 <= mi < 60:
            return dt_time(h, mi)
        return None

    # ------------------------------------------------------------------ #
    #  Сохранение в БД                                                   #
    # ------------------------------------------------------------------ #

    def _get_category(self, category_name):
        """
        Ищет категорию по фиксированному slug (CATEGORY_SLUGS).
        Если категории нет — возвращает None. НИЧЕГО НЕ СОЗДАЁТ.
        """
        slug = CATEGORY_SLUGS.get(
            category_name,
            slugify(category_name)[:100] or 'other',
        )
        return Category.objects.filter(slug=slug).first()

    def _get_place(self, place_name):
        """
        Возвращает Place по имени.
        Если такого нет — создаёт с уникальным slug.
        """
        place = Place.objects.filter(name=place_name).first()
        if place is not None:
            return place

        place = Place.objects.create(
            name=place_name,
            slug=self._unique_slug(Place, place_name),
        )
        return place

    @transaction.atomic
    def _save_event(self, parsed, category):
        """
        Сохраняет событие. `category` может быть None —
        тогда событие сохранится без категории.
        """
        place = self._get_place(parsed['place_name'])

        exists = Event.objects.filter(
            title=parsed['title'],
            start_date=parsed['start_date'],
        ).exists()
        if exists:
            return False

        Event.objects.create(
            title=parsed['title'],
            category=category,  # может быть None
            place=place,
            description_short=parsed['description_short'],
            description=parsed['description'],
            start_date=parsed['start_date'],
            end_date=parsed['end_date'],
            start_time=parsed['start_time'],
            status=Event.Status.MODERATION,
            age_restriction=Event.AgeRestriction.SIXTEEN,
            is_free=False,
        )
        return True

    def _unique_slug(self, model, name):
        base = slugify(name)[:200] or 'place'
        slug = base
        i = 1
        while model.objects.filter(slug=slug).exists():
            slug = f'{base}-{i}'
            i += 1
        return slug