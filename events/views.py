"""Представления приложения events."""
from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import EmptyPage
from django.db.models import (
    Q, Case, When, Value, IntegerField, Count, DateField,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView,
)

from .forms import EventForm, EventImageFormSet
from .models import Event, Category, Place


# ======================================================================
#  Кэш
# ======================================================================

def invalidate_event_cache():
    """Сбрасывает кэш счётчиков."""
    cache.delete('events_published_count')
    cache.delete('categories_active_count')


# ======================================================================
#  ПУБЛИЧНЫЕ
# ======================================================================

class EventList(ListView):
    """Афиша событий с пагинацией, фильтрами и сортировкой."""
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            Event.objects
            .filter(status=Event.Status.PUBLISHED)
            .annotate(
                event_end=Coalesce(
                    'end_date', 'start_date', output_field=DateField()
                )
            )
        )

        today = timezone.localdate()
        date_filter = self.request.GET.get('date_filter', '')
        start_date_raw = self.request.GET.get('start_date')
        end_date_raw = self.request.GET.get('end_date')
        has_range = bool(start_date_raw or end_date_raw)

        def parse_date(value):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return None

        start_date_obj = parse_date(start_date_raw) if start_date_raw else None
        end_date_obj = parse_date(end_date_raw) if end_date_raw else None

        def overlaps(qs, range_start, range_end):
            return qs.filter(
                start_date__lte=range_end,
                event_end__gte=range_start,
            )

        # ---------- Фильтры по датам ----------
        if has_range:
            if start_date_obj and end_date_obj:
                queryset = overlaps(queryset, start_date_obj, end_date_obj)
            elif start_date_obj:
                queryset = queryset.filter(event_end__gte=start_date_obj)
            elif end_date_obj:
                queryset = queryset.filter(start_date__lte=end_date_obj)
            date_filter = ''
        elif date_filter == 'past':
            queryset = queryset.filter(event_end__lt=today)
        elif date_filter == 'today':
            queryset = overlaps(queryset, today, today)
        elif date_filter == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            queryset = overlaps(queryset, tomorrow, tomorrow)
        elif date_filter == 'week':
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            queryset = overlaps(queryset, start_of_week, end_of_week)
        elif date_filter == 'weekend':
            days_until_saturday = (5 - today.weekday()) % 7
            saturday = today + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            queryset = overlaps(queryset, saturday, sunday)
        elif date_filter == 'month':
            if today.month == 12:
                end_of_month = today.replace(
                    year=today.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                end_of_month = today.replace(
                    month=today.month + 1, day=1
                ) - timedelta(days=1)
            queryset = overlaps(queryset, today, end_of_month)
        else:
            queryset = queryset.filter(event_end__gte=today)

        # ---------- Поиск ----------
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description_short__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # ---------- Категория ----------
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # ---------- Приоритет «идёт сейчас» ----------
        if date_filter != 'past':
            is_ongoing = Q(start_date__lte=today, event_end__gte=today)
            queryset = queryset.annotate(
                ongoing=Case(
                    When(is_ongoing, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )

        queryset = queryset.select_related('category', 'place')

        # ---------- Сортировка ----------
        sort = self.request.GET.get('sort', 'date')

        if date_filter == 'past':
            queryset = queryset.order_by('-start_date', '-start_time', 'id')
        else:
            if sort == 'popular':
                queryset = queryset.order_by(
                    'ongoing', 'start_date', 'start_time', 'id'
                )
            elif sort == 'price_asc':
                queryset = queryset.order_by(
                    'ongoing',
                    Case(
                        When(price=0, then=Value(0)),
                        When(price__isnull=True, then=Value(2)),
                        default=Value(1),
                        output_field=IntegerField(),
                    ),
                    'price',
                    'start_date', 'start_time', 'id',
                )
            elif sort == 'price_desc':
                queryset = queryset.order_by(
                    'ongoing',
                    Case(
                        When(price__isnull=True, then=Value(2)),
                        When(price=0, then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    ),
                    '-price',
                    'start_date', 'start_time', 'id',
                )
            else:
                queryset = queryset.order_by(
                    'ongoing', 'start_date', 'start_time', 'id'
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['categories'] = Category.objects.filter(is_active=True)

        events_count = cache.get('events_published_count')
        if events_count is None:
            events_count = Event.objects.filter(
                status=Event.Status.PUBLISHED
            ).count()
            cache.set('events_published_count', events_count, 300)
        context['events_count'] = events_count

        categories_count = cache.get('categories_active_count')
        if categories_count is None:
            categories_count = Category.objects.filter(is_active=True).count()
            cache.set('categories_active_count', categories_count, 300)
        context['categories_count'] = categories_count

        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['date_filter'] = self.request.GET.get('date_filter', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['sort'] = self.request.GET.get('sort', 'date')
        return context


class EventDetailView(DetailView):
    """Детальная страница события."""
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return (
            Event.objects
            .filter(status=Event.Status.PUBLISHED)
            .select_related('category', 'place')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        today = timezone.localdate()

        similar_limit = 4
        similar = []

        if event.category_id:
            similar = list(
                Event.objects
                .filter(
                    status=Event.Status.PUBLISHED,
                    category_id=event.category_id,
                )
                .exclude(pk=event.pk)
                .annotate(
                    event_end=Coalesce(
                        'end_date', 'start_date', output_field=DateField()
                    )
                )
                .filter(event_end__gte=today)
                .select_related('category', 'place')
                .order_by('start_date', 'start_time')[:similar_limit]
            )

        if len(similar) < similar_limit:
            exclude_ids = [event.pk] + [e.pk for e in similar]
            fallback = (
                Event.objects
                .filter(status=Event.Status.PUBLISHED)
                .exclude(pk__in=exclude_ids)
                .annotate(
                    event_end=Coalesce(
                        'end_date', 'start_date', output_field=DateField()
                    )
                )
                .filter(event_end__gte=today)
                .select_related('category', 'place')
                .order_by('-created_at')[:similar_limit - len(similar)]
            )
            similar.extend(fallback)

        context['similar_events'] = similar
        context['categories'] = Category.objects.filter(is_active=True)
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['date_filter'] = self.request.GET.get('date_filter', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['sort'] = self.request.GET.get('sort', 'date')

        return context


# ======================================================================
#  УПРАВЛЕНИЕ
# ======================================================================

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Доступ только для staff / superuser."""
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_staff or user.is_superuser)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class EventManageListView(StaffRequiredMixin, ListView):
    """Список событий для управления (staff)."""
    model = Event
    template_name = 'events/event_manage_list.html'
    context_object_name = 'events'
    paginate_by = 50

    def get_queryset(self):
        qs = Event.objects.select_related('category', 'place')

        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description_short__icontains=search) |
                Q(place__name__icontains=search)
            )

        status = self.request.GET.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)

        category = self.request.GET.get('category', '').strip()
        if category:
            qs = qs.filter(category__slug=category)

        sort = self.request.GET.get('sort', '-updated_at')
        allowed_sorts = {
            '-updated_at': '-updated_at',
            'updated_at': 'updated_at',
            'start_date': 'start_date',
            '-start_date': '-start_date',
            'title': 'title',
        }
        qs = qs.order_by(allowed_sorts.get(sort, '-updated_at'))
        return qs

    def paginate_queryset(self, queryset, page_size):
        """При выходе страницы за диапазон — последняя, а не 404."""
        paginator = self.get_paginator(
            queryset,
            page_size,
            orphans=self.get_paginate_orphans(),
            allow_empty_first_page=self.get_allow_empty(),
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except (TypeError, ValueError):
            page_number = 1
        if page_number < 1:
            page_number = 1
        num_pages = paginator.num_pages
        if num_pages > 0 and page_number > num_pages:
            page_number = num_pages
        try:
            page_obj = paginator.page(page_number)
            return (paginator, page_obj, page_obj.object_list, page_obj.has_other_pages())
        except EmptyPage:
            page_obj = paginator.page(1)
            return (paginator, page_obj, page_obj.object_list, page_obj.has_other_pages())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        counts = Event.objects.aggregate(
            all=Count('id'),
            draft=Count('id', filter=Q(status=Event.Status.DRAFT)),
            moderation=Count('id', filter=Q(status=Event.Status.MODERATION)),
            published=Count('id', filter=Q(status=Event.Status.PUBLISHED)),
        )

        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['sort'] = self.request.GET.get('sort', '-updated_at')
        context['statuses'] = Event.Status.choices
        context['all_categories'] = Category.objects.filter(is_active=True)
        context['counts'] = counts
        return context


class EventCreateView(StaffRequiredMixin, CreateView):
    """Создание события вместе с галереей изображений."""
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Новое событие'
        context['submit_label'] = 'Создать'
        context['is_edit'] = False

        if self.request.POST:
            context['image_formset'] = EventImageFormSet(
                self.request.POST, self.request.FILES
            )
        else:
            context['image_formset'] = EventImageFormSet()
        return context

    def form_valid(self, form):
        image_formset = EventImageFormSet(
            self.request.POST, self.request.FILES
        )
        if not image_formset.is_valid():
            return self.form_invalid(form)

        self.object = form.save()
        image_formset.instance = self.object
        image_formset.save()

        invalidate_event_cache()
        messages.success(self.request, f'Событие «{self.object.title}» создано.')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('events:event_list_manage')


class EventUpdateView(StaffRequiredMixin, UpdateView):
    """Редактирование события вместе с галереей."""
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Event.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Редактирование: {self.object.title}'
        context['submit_label'] = 'Сохранить'
        context['is_edit'] = True
        context['public_url'] = reverse(
            'events:event_detail', kwargs={'slug': self.object.slug}
        )

        if self.request.POST:
            context['image_formset'] = EventImageFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            context['image_formset'] = EventImageFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        image_formset = EventImageFormSet(
            self.request.POST, self.request.FILES, instance=self.object
        )
        if not image_formset.is_valid():
            return self.form_invalid(form)

        self.object = form.save()
        image_formset.save()

        invalidate_event_cache()
        messages.success(self.request, f'Событие «{self.object.title}» сохранено.')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('events:event_list_manage')


class EventBulkActionView(StaffRequiredMixin, View):
    """
    Массовые действия над выбранными событиями.
    """

    MAX_BULK = 100

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', '')
        ids = request.POST.getlist('ids')

        if not ids:
            messages.warning(request, 'Ничего не выбрано.')
            return self._redirect_back(request)

        if len(ids) > self.MAX_BULK:
            messages.error(
                request,
                f'За раз можно обработать не более {self.MAX_BULK} событий. '
                f'Выбрано: {len(ids)}.'
            )
            return self._redirect_back(request)

        qs = Event.objects.filter(pk__in=ids)

        if action == 'publish':
            updated = qs.update(
                status=Event.Status.PUBLISHED, updated_at=timezone.now()
            )
            invalidate_event_cache()
            messages.success(request, f'Опубликовано: {updated}.')

        elif action == 'moderation':
            updated = qs.update(
                status=Event.Status.MODERATION, updated_at=timezone.now()
            )
            invalidate_event_cache()
            messages.success(request, f'Отправлено на модерацию: {updated}.')

        elif action == 'draft':
            updated = qs.update(
                status=Event.Status.DRAFT, updated_at=timezone.now()
            )
            invalidate_event_cache()
            messages.success(request, f'Снято в черновики: {updated}.')

        elif action == 'delete':
            count, _ = qs.delete()
            invalidate_event_cache()
            messages.success(request, f'Удалено: {count}.')

        else:
            messages.error(request, 'Неизвестное действие.')

        return self._redirect_back(request)

    @staticmethod
    def _redirect_back(request):
        """Возврат на страницу управления с сохранением фильтров."""
        referer = request.META.get('HTTP_REFERER', '')
        if referer and 'manage' in referer:
            return redirect(referer)
        return redirect(reverse('events:event_list_manage'))

# ======================================================================
#  ПЛОЩАДКА
# ======================================================================
from datetime import date
from calendar import monthrange


class PlaceDetailView(DetailView):
    """Страница площадки: описание, адрес, расписание событий."""
    model = Place
    template_name = 'events/place_detail.html'
    context_object_name = 'place'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Place.objects.all()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()
        slug = self.kwargs.get(self.slug_url_kwarg)
        return get_object_or_404(queryset, slug=slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        place = self.object
        today = timezone.localdate()

        # ---------- Параметр месяца ----------
        month_param = self.request.GET.get('month', '').strip()
        selected_year, selected_month = self._parse_month(month_param, today)

        # Границы выбранного месяца
        month_start = date(selected_year, selected_month, 1)
        _, last_day = monthrange(selected_year, selected_month)
        month_end = date(selected_year, selected_month, last_day)

        # ---------- События выбранного месяца ----------
        events = list(
            Event.objects
            .filter(status=Event.Status.PUBLISHED, place=place)
            .annotate(
                event_end=Coalesce(
                    'end_date', 'start_date', output_field=DateField()
                )
            )
            .filter(
                event_end__gte=month_start,
                start_date__lte=month_end,
            )
            .select_related('category', 'place')
            .order_by('start_date', 'start_time')
        )

        # ---------- Группировка ----------
        is_current_month = (
            selected_year == today.year and selected_month == today.month
        )
        schedule = self._group_by_date(
            events, today, hide_past=is_current_month, place=place
        )

        # ---------- Прошедшие события ----------
        past = (
            Event.objects
            .filter(status=Event.Status.PUBLISHED, place=place)
            .annotate(
                event_end=Coalesce(
                    'end_date', 'start_date', output_field=DateField()
                )
            )
            .filter(event_end__lt=today)
            .select_related('category', 'place')
            .order_by('-start_date', '-start_time')[:6]
        )

        # ---------- Доступные месяцы ----------
        available_months = self._get_available_months(place, today)

        # ---------- Часы работы ----------
        working_hours = place.working_hours_display()

        context['schedule'] = schedule
        context['past_events'] = past
        context['total_upcoming'] = len(events)
        context['selected_month'] = f'{selected_year:04d}-{selected_month:02d}'
        context['available_months'] = available_months
        context['month_label'] = self._month_label(selected_year, selected_month)
        context['working_hours'] = working_hours
        return context

    # ------------------------------------------------------------------
    #  Хелперы
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_month(raw, today):
        """Парсит 'YYYY-MM'. Если невалидно — текущий месяц."""
        if raw:
            try:
                year, month = map(int, raw.split('-'))
                if 1 <= month <= 12 and year >= 2000:
                    return year, month
            except (ValueError, AttributeError):
                pass
        return today.year, today.month

    @staticmethod
    def _month_label(year, month):
        MONTHS_GEN = [
            '', 'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
            'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь',
        ]
        return f'{MONTHS_GEN[month]} {year}'

    @staticmethod
    def _get_available_months(place, today):
        """Возвращает список месяцев с предстоящими событиями (от старых к новым).

        Длительные события, начавшиеся в прошлом, отображаются по текущему
        месяцу, а не по месяцу старта — чтобы прошедшие месяцы не появлялись
        в фильтре.
        """
        months_raw = (
            Event.objects
            .filter(status=Event.Status.PUBLISHED, place=place)
            .annotate(
                event_end=Coalesce(
                    'end_date', 'start_date', output_field=DateField()
                )
            )
            .filter(event_end__gte=today)
            .values_list('start_date__year', 'start_date__month')
            .distinct()
            .order_by('start_date__year', 'start_date__month')
        )

        MONTHS_NOM = [
            '', 'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
            'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь',
        ]

        current_ym = (today.year, today.month)

        result = []
        for year, month in months_raw:
            if (year, month) < current_ym:
                continue
            result.append({
                'value': f'{year:04d}-{month:02d}',
                'label': f'{MONTHS_NOM[month]} {year}',
            })
        return result

    @staticmethod
    def _group_by_date(events, today, hide_past=False, place=None):
        """Группирует события по дням.

        Если hide_past=True — прошедшие дни не включаются в расписание.
        Длительные события показываются только в рабочие дни площадки.
        Однодневные — всегда.
        """
        by_date = defaultdict(list)

        for event in events:
            start = event.start_date
            end = event.end_date or event.start_date
            if end < start:
                end = start

            is_long = end > start

            current = start
            while current <= end:
                if hide_past and current < today:
                    current += timedelta(days=1)
                    continue

                # Длительные события — только в рабочие дни
                if is_long and place and not place.is_open_on(current):
                    current += timedelta(days=1)
                    continue

                by_date[current].append(event)
                current += timedelta(days=1)

        WEEKDAYS = [
            'понедельник', 'вторник', 'среда', 'четверг',
            'пятница', 'суббота', 'воскресенье',
        ]
        MONTHS = [
            '', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
        ]

        schedule = []
        for d in sorted(by_date.keys()):
            delta = (d - today).days

            if delta == 0:
                label = 'Сегодня'
            elif delta == 1:
                label = 'Завтра'
            elif delta == 2:
                label = 'Послезавтра'
            else:
                label = f'{d.day} {MONTHS[d.month]}'

            day_events = sorted(
                by_date[d],
                key=lambda e: (
                    e.start_time is None,
                    e.start_time or datetime.min.time(),
                ),
            )

            schedule.append({
                'date': d,
                'label': label,
                'weekday': WEEKDAYS[d.weekday()],
                'is_today': delta == 0,
                'is_weekend': d.weekday() >= 5,
                'events': day_events,
            })

        return schedule
