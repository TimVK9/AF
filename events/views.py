# views.py

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Case, When, Value, IntegerField, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, View,
)

from .analytics import track_view, get_event_total_views
from .forms import EventForm, EventImageFormSet
from .models import Event, Category, Place


# ======================================================================
#  ПУБЛИЧНЫЕ
# ======================================================================

class EventList(ListView):
    """
    Список событий с классической пагинацией.

    Событие может длиться несколько дней (start_date ... end_date).
    В фильтры попадает, если его интервал пересекается с интервалом фильтра.
    Если end_date пустой — считаем событие однодневным (event_end = start_date).
    """
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12

    def get(self, request, *args, **kwargs):
        """Обезличенная статистика просмотров главной, категорий и поиска."""
        if request.resolver_match.url_name == "home":
            if not request.GET:
                track_view("home")
            elif request.GET.get("category"):
                slug = request.GET["category"]
                try:
                    cat = Category.objects.only("id").get(slug=slug)
                    track_view("category", cat.id)
                except Category.DoesNotExist:
                    pass
            elif request.GET.get("search"):
                track_view("search")

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()

        queryset = queryset.filter(status=Event.Status.PUBLISHED)

        event_end = Coalesce('end_date', 'start_date')
        queryset = queryset.annotate(event_end=event_end)

        today = timezone.localdate()
        date_filter = self.request.GET.get('date_filter', '')
        start_date_raw = self.request.GET.get('start_date')
        end_date_raw = self.request.GET.get('end_date')
        has_range = bool(start_date_raw or end_date_raw)

        if not has_range:
            if date_filter == 'past':
                queryset = queryset.filter(event_end__lt=today)
            else:
                queryset = queryset.filter(event_end__gte=today)

        def overlaps(qs, range_start, range_end):
            return qs.filter(
                start_date__lte=range_end,
                event_end__gte=range_start,
            )

        if date_filter == 'today':
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

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description_short__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        def parse_date(value):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return None

        start_date_obj = parse_date(start_date_raw) if start_date_raw else None
        end_date_obj = parse_date(end_date_raw) if end_date_raw else None

        if start_date_obj and end_date_obj:
            queryset = overlaps(queryset, start_date_obj, end_date_obj)
        elif start_date_obj:
            queryset = queryset.filter(event_end__gte=start_date_obj)
        elif end_date_obj:
            queryset = queryset.filter(start_date__lte=end_date_obj)

        # ------------------------------------------------------------------
        # Аннотация один раз — до сортировки
        # ------------------------------------------------------------------
        queryset = (
            queryset
            .annotate(views_total=Coalesce(Sum('views__count'), Value(0)))
            .select_related('category', 'place')
        )

        # ------------------------------------------------------------------
        # Сортировка
        # ------------------------------------------------------------------
        sort = self.request.GET.get('sort', 'date')

        if date_filter == 'past':
            if sort == 'popular':
                queryset = queryset.order_by('-views_total', '-start_date')
            else:
                queryset = queryset.order_by('-start_date', '-start_time')
        else:
            if sort == 'popular':
                queryset = queryset.order_by('-views_total', '-start_date')
            elif sort == 'price_asc':
                queryset = queryset.order_by(
                    Case(
                        When(is_free=True, then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    ),
                    'price',
                    'start_date',
                )
            elif sort == 'price_desc':
                queryset = queryset.order_by('-price', 'start_date')
            else:
                queryset = queryset.order_by('start_date', 'start_time')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["categories"] = Category.objects.filter(is_active=True)

        context["events_count"] = Event.objects.filter(
            status=Event.Status.PUBLISHED
        ).count()
        context["categories_count"] = Category.objects.filter(
            is_active=True
        ).count()

        context["selected_category"] = self.request.GET.get('category', '')
        context["search_query"] = self.request.GET.get('search', '')
        context["date_filter"] = self.request.GET.get('date_filter', '')
        context["start_date"] = self.request.GET.get('start_date', '')
        context["end_date"] = self.request.GET.get('end_date', '')
        context["sort"] = self.request.GET.get('sort', 'date')

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

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        obj = get_object_or_404(queryset, slug=slug)

        # Только дневной счётчик. Больше никаких UPDATE на Event.
        track_view("event", obj.pk)

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object

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
                .select_related('category', 'place')
                .order_by('start_date', 'start_time')[:similar_limit]
            )

        if len(similar) < similar_limit:
            exclude_ids = [event.pk] + [e.pk for e in similar]
            fallback = (
                Event.objects
                .filter(status=Event.Status.PUBLISHED)
                .exclude(pk__in=exclude_ids)
                .select_related('category', 'place')
                .order_by('-created_at')[:similar_limit - len(similar)]
            )
            similar.extend(fallback)

        context['similar_events'] = similar
        context['event_views_total'] = get_event_total_views(event.pk)

        # Контекст для фильтров
        context["categories"] = Category.objects.filter(is_active=True)
        context["selected_category"] = self.request.GET.get('category', '')
        context["search_query"] = self.request.GET.get('search', '')
        context["date_filter"] = self.request.GET.get('date_filter', '')
        context["start_date"] = self.request.GET.get('start_date', '')
        context["end_date"] = self.request.GET.get('end_date', '')
        context["sort"] = self.request.GET.get('sort', 'date')

        return context


# ======================================================================
#  УПРАВЛЕНИЕ
# ======================================================================

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_staff or user.is_superuser)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied
        return super().handle_no_permission()


class EventManageListView(StaffRequiredMixin, ListView):
    model = Event
    template_name = 'events/event_manage_list.html'
    context_object_name = 'events'
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Event.all_objects
            .select_related('category', 'place')
        )

        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description_short__icontains=search) |
                Q(place__name__icontains=search)
            )

        status = self.request.GET.get('status', '').strip()
        if status in dict(Event.Status.choices):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['category_filter'] = self.request.GET.get('category', '')
        context['sort'] = self.request.GET.get('sort', '-updated_at')
        context['statuses'] = Event.Status.choices
        context['all_categories'] = Category.objects.filter(is_active=True)
        context['counts'] = {
            'all': Event.all_objects.count(),
            'draft': Event.all_objects.filter(status=Event.Status.DRAFT).count(),
            'moderation': Event.all_objects.filter(status=Event.Status.MODERATION).count(),
            'published': Event.all_objects.filter(status=Event.Status.PUBLISHED).count(),
            'cancelled': Event.all_objects.filter(status=Event.Status.CANCELLED).count(),
            'finished': Event.all_objects.filter(status=Event.Status.FINISHED).count(),
        }
        return context


class EventCreateView(StaffRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Новое событие'
        context['submit_label'] = 'Создать и открыть'
        context['is_edit'] = False

        if self.request.POST:
            context['image_formset'] = EventImageFormSet(
                self.request.POST, self.request.FILES
            )
        else:
            context['image_formset'] = EventImageFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        if not image_formset.is_valid():
            return self.form_invalid(form)

        self.object = form.save()
        image_formset.instance = self.object
        image_formset.save()

        messages.success(
            self.request,
            f'Событие «{self.object.title}» создано.'
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('events:event_update', kwargs={'slug': self.object.slug})


class EventUpdateView(StaffRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

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
        context = self.get_context_data()
        image_formset = context['image_formset']
        if not image_formset.is_valid():
            return self.form_invalid(form)

        self.object = form.save()
        image_formset.instance = self.object
        image_formset.save()

        messages.success(
            self.request,
            f'Событие «{self.object.title}» сохранено.'
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('events:event_update', kwargs={'slug': self.object.slug})


class EventBulkActionView(StaffRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', '')
        ids = request.POST.getlist('ids')

        if not ids:
            messages.warning(request, 'Ничего не выбрано.')
            return redirect('events:event_list_manage')

        qs = Event.all_objects.filter(pk__in=ids)

        if action == 'publish':
            updated = qs.update(status=Event.Status.PUBLISHED)
            messages.success(request, f'Опубликовано: {updated}.')
        elif action == 'draft':
            updated = qs.update(status=Event.Status.DRAFT)
            messages.success(request, f'Снято в черновики: {updated}.')
        elif action == 'cancel':
            updated = qs.update(status=Event.Status.CANCELLED)
            messages.success(request, f'Отменено: {updated}.')
        elif action == 'delete':
            count = 0
            for event in qs:
                if not event.is_deleted:
                    event.delete()
                    count += 1
            messages.success(request, f'Удалено: {count}.')
        else:
            messages.error(request, 'Неизвестное действие.')

        return redirect('events:event_list_manage')


# ======================================================================
#  ПЛОЩАДКА
# ======================================================================

class PlaceDetailView(DetailView):
    """
    Страница площадки: описание, адрес, контакты,
    расписание предстоящих событий по дням.
    """
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
        obj = get_object_or_404(queryset, slug=slug)
        track_view('place', obj.pk)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        place = self.object
        today = timezone.localdate()

        # Горизонт расписания — 60 дней вперёд
        horizon = today + timedelta(days=60)

        events = list(
            Event.objects
            .filter(
                status=Event.Status.PUBLISHED,
                place=place,
            )
            .annotate(event_end=Coalesce('end_date', 'start_date'))
            .filter(event_end__gte=today, start_date__lte=horizon)
            .select_related('category', 'place')
            .order_by('start_date', 'start_time')
        )

        # Группировка по датам
        schedule = self._group_by_date(events, today)

        # Прошедшие события
        past = (
            Event.objects
            .filter(
                status__in=[
                    Event.Status.PUBLISHED,
                    Event.Status.FINISHED,
                ],
                place=place,
            )
            .annotate(event_end=Coalesce('end_date', 'start_date'))
            .filter(event_end__lt=today)
            .select_related('category', 'place')
            .order_by('-start_date', '-start_time')[:6]
        )

        context['schedule'] = schedule
        context['past_events'] = past
        context['total_upcoming'] = len(events)

        return context

    @staticmethod
    def _group_by_date(events, today):
        """
        Группирует события по датам.

        Событие попадает в каждую дату своего интервала — если это
        многодневная выставка, она видна под каждым днём её проведения.
        """
        from collections import defaultdict

        by_date = defaultdict(list)

        for event in events:
            start = event.start_date
            end = event.end_date or event.start_date
            if end < start:
                end = start

            current = start
            while current <= end:
                if current >= today:
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