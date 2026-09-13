from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import (
    Q, Case, When, Value, IntegerField, F,
)
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, View,
)

from .analytics import track_view
from .forms import EventForm, EventImageFormSet
from .models import Event, Category, Place


# ======================================================================
#  ПУБЛИЧНЫЕ
# ======================================================================

class EventList(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12

    def get(self, request, *args, **kwargs):
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
        queryset = super().get_queryset().filter(status=Event.Status.PUBLISHED)

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
                end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
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

        sort = self.request.GET.get('sort', 'date')

        if date_filter == 'past':
            if sort == 'popular':
                queryset = queryset.order_by('-views_count', '-favorites_count')
            else:
                queryset = queryset.order_by('-start_date', '-start_time')
        else:
            if sort == 'popular':
                queryset = queryset.order_by('-views_count', '-favorites_count')
            elif sort == 'price_asc':
                queryset = queryset.order_by(
                    Case(When(is_free=True, then=Value(0)), default=Value(1), output_field=IntegerField()),
                    'price', 'start_date',
                )
            elif sort == 'price_desc':
                queryset = queryset.order_by('-price', 'start_date')
            else:
                queryset = queryset.order_by('start_date', 'start_time')

        return queryset.select_related('category', 'place').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["events_count"] = Event.objects.filter(status=Event.Status.PUBLISHED).count()
        context["categories_count"] = Category.objects.count()
        context["selected_category"] = self.request.GET.get('category', '')
        context["search_query"] = self.request.GET.get('search', '')
        context["date_filter"] = self.request.GET.get('date_filter', '')
        context["start_date"] = self.request.GET.get('start_date', '')
        context["end_date"] = self.request.GET.get('end_date', '')
        context["sort"] = self.request.GET.get('sort', 'date')
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return (
            Event.objects
            .filter(status=Event.Status.PUBLISHED)
            .select_related('category', 'place', 'place__address')
        )

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg)
        obj = get_object_or_404(queryset, slug=slug)

        Event.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
        obj.views_count += 1
        track_view("event", obj.pk)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object

        similar_limit = 4
        similar = []

        # ------------------------------------------------------------------
        # Шаг 1: похожие по категории — ближайшие по дате начала
        # ------------------------------------------------------------------
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

        # ------------------------------------------------------------------
        # Шаг 2: если по категории не хватило — добираем популярными
        # ------------------------------------------------------------------
        if len(similar) < similar_limit:
            exclude_ids = [event.pk] + [e.pk for e in similar]
            fallback = (
                Event.objects
                .filter(status=Event.Status.PUBLISHED)
                .exclude(pk__in=exclude_ids)
                .select_related('category', 'place')
                .order_by('-views_count', '-created_at')[:similar_limit - len(similar)]
            )
            similar.extend(fallback)

        context['similar_events'] = similar

        # ------------------------------------------------------------------
        # Контекст для фильтров — нужен, чтобы нижнее меню и оверлеи
        # работали и на детальной странице
        # ------------------------------------------------------------------
        context["categories"] = Category.objects.all()
        context["selected_category"] = self.request.GET.get('category', '')
        context["search_query"] = self.request.GET.get('search', '')
        context["date_filter"] = self.request.GET.get('date_filter', '')
        context["start_date"] = self.request.GET.get('start_date', '')
        context["end_date"] = self.request.GET.get('end_date', '')
        context["sort"] = self.request.GET.get('sort', 'date')

        return context


# ======================================================================
#  УПРАВЛЕНИЕ (только staff / superuser)
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
        qs = Event.objects.select_related('category', 'place')

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
            '-views_count': '-views_count',
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
        context['all_categories'] = Category.objects.all()
        context['counts'] = {
            'all': Event.objects.count(),
            'draft': Event.objects.filter(status=Event.Status.DRAFT).count(),
            'moderation': Event.objects.filter(status=Event.Status.MODERATION).count(),
            'published': Event.objects.filter(status=Event.Status.PUBLISHED).count(),
            'cancelled': Event.objects.filter(status=Event.Status.CANCELLED).count(),
            'finished': Event.objects.filter(status=Event.Status.FINISHED).count(),
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
            context['image_formset'] = EventImageFormSet(self.request.POST, self.request.FILES)
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

        messages.success(self.request, f'Событие «{self.object.title}» создано.')
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
        context['public_url'] = reverse('events:event_detail', kwargs={'slug': self.object.slug})

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

        messages.success(self.request, f'Событие «{self.object.title}» сохранено.')
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

        qs = Event.objects.filter(pk__in=ids)

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
            count = qs.count()
            qs.delete()
            messages.success(request, f'Удалено: {count}.')
        else:
            messages.error(request, 'Неизвестное действие.')

        return redirect('events:event_list_manage')


# ======================================================================
#  ОБРАБОТЧИК CSRF-ОШИБКИ (403)
# ======================================================================

def csrf_failure(request, reason=""):
    """
    Кастомная страница ошибки CSRF (403).
    Django рендерит её, когда CSRF-токен невалиден или отсутствует.
    """
    return render(
        request,
        "403_csrf.html",
        {"reason": reason},
        status=403,
    )

"""
Служебные вью для админки: запуск парсера, просмотр логов.
"""

from io import StringIO

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import ImportLog, Event


@staff_member_required
def run_import_kultisk(request):
    """
    GET  — показывает страницу с кнопкой подтверждения.
    POST — запускает команду и сохраняет результат в ImportLog.
    """
    if request.method == 'POST':
        return _run_import(request)

    # Предпросмотр: сколько событий сейчас в moderation
    moderation_count = Event.objects.filter(
        status=Event.Status.MODERATION
    ).count()

    last_logs = ImportLog.objects.filter(source=ImportLog.Source.KULTISK)[:5]

    return render(request, 'admin/run_import.html', {
        'title': 'Импорт афиши с kultisk.ru',
        'moderation_count': moderation_count,
        'last_logs': last_logs,
    })


def _run_import(request):
    """Запускает команду, ловит вывод, сохраняет в ImportLog."""
    log = ImportLog.objects.create(
        source=ImportLog.Source.KULTISK,
        status=ImportLog.Status.RUNNING,
        created_by=request.user,
    )

    stdout = StringIO()
    stderr = StringIO()

    try:
        call_command(
            'parse_kultisk_afisha',
            stdout=stdout,
            stderr=stderr,
        )
        log.status = ImportLog.Status.SUCCESS
    except Exception as exc:
        log.status = ImportLog.Status.ERROR
        stderr.write(f'\n\nОшибка: {exc}\n')

    output = stdout.getvalue()
    errors = stderr.getvalue()
    log.log_output = output + ('\n\n' + errors if errors else '')
    log.finished_at = timezone.now()

    # Парсим счётчики из вывода (если команда их печатает)
    log.events_created = _extract_int(output, 'Создано:')
    log.events_skipped = _extract_int(output, 'пропущено (дубли):')
    log.rows_parsed = _extract_int(output, 'Разобрано строк:')
    log.rows_skipped = _extract_int(output, 'Пропущено (не распознал дату):')

    log.save()

    if log.status == ImportLog.Status.SUCCESS:
        messages.success(
            request,
            f'Импорт завершён. Создано: {log.events_created}, '
            f'пропущено: {log.events_skipped}.',
        )
    else:
        messages.error(request, 'Импорт завершился с ошибкой. Смотри лог.')

    return redirect('admin:events_importlog_change', log.pk)


def _extract_int(text, prefix):
    """Достаёт число после 'prefix' из текста."""
    import re
    m = re.search(rf'{re.escape(prefix)}\s*(\d+)', text)
    return int(m.group(1)) if m else 0