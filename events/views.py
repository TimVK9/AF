# views.py
from datetime import datetime, timedelta

from django.db.models import Q, Case, When, Value, IntegerField, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .models import Event, Category, Place
from .analytics import track_view


class EventList(ListView):
    """Список событий с классической пагинацией"""
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12

    def get(self, request, *args, **kwargs):
        """
        Обезличенная статистика просмотров главной, категорий и поиска.
        Вызывается до рендера, поэтому счётчик увеличивается один раз за запрос.
        """
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

        # Показываем только опубликованные события
        queryset = queryset.filter(status=Event.Status.PUBLISHED)

        today = timezone.localdate()
        date_filter = self.request.GET.get('date_filter', '')

        # ===== БАЗОВАЯ ЛОГИКА: ориентируемся только на start_date =====
        if date_filter == 'past':
            queryset = queryset.filter(start_date__lt=today)
        else:
            queryset = queryset.filter(start_date__gte=today)

        # ===== ДОПОЛНИТЕЛЬНЫЕ ФИЛЬТРЫ ПО ДАТЕ =====
        if date_filter == 'today':
            queryset = queryset.filter(start_date=today)

        elif date_filter == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            queryset = queryset.filter(start_date=tomorrow)

        elif date_filter == 'week':
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            queryset = queryset.filter(
                start_date__gte=start_of_week,
                start_date__lte=end_of_week
            )

        elif date_filter == 'weekend':
            days_until_saturday = (5 - today.weekday()) % 7
            saturday = today + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            queryset = queryset.filter(
                start_date__gte=saturday,
                start_date__lte=sunday
            )

        elif date_filter == 'month':
            if today.month == 12:
                end_of_month = today.replace(
                    year=today.year + 1, month=1, day=1
                ) - timedelta(days=1)
            else:
                end_of_month = today.replace(
                    month=today.month + 1, day=1
                ) - timedelta(days=1)
            queryset = queryset.filter(
                start_date__gte=today,
                start_date__lte=end_of_month
            )

        # ===== ПОИСК =====
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description_short__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # ===== КАТЕГОРИЯ =====
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # ===== ДИАПАЗОН ДАТ =====
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date and end_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    start_date__gte=start_date_obj,
                    start_date__lte=end_date_obj
                )
            except (ValueError, TypeError):
                pass
        elif start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(start_date__gte=start_date_obj)
            except (ValueError, TypeError):
                pass
        elif end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(start_date__lte=end_date_obj)
            except (ValueError, TypeError):
                pass

        # ===== СОРТИРОВКА =====
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
                    Case(
                        When(is_free=True, then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    ),
                    'price',
                    'start_date'
                )
            elif sort == 'price_desc':
                queryset = queryset.order_by('-price', 'start_date')
            else:
                queryset = queryset.order_by('start_date', 'start_time')

        return queryset.select_related('category', 'place').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["categories"] = Category.objects.all()
        context["events_count"] = Event.objects.filter(
            status=Event.Status.PUBLISHED
        ).count()
        context["categories_count"] = Category.objects.count()

        context["selected_category"] = self.request.GET.get('category', '')
        context["search_query"] = self.request.GET.get('search', '')
        context["date_filter"] = self.request.GET.get('date_filter', '')
        context["start_date"] = self.request.GET.get('start_date', '')
        context["end_date"] = self.request.GET.get('end_date', '')
        context["sort"] = self.request.GET.get('sort', 'date')

        return context


class EventDetailView(DetailView):
    """Детальная страница события"""
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

        # Основной счётчик просмотров (в самой модели Event)
        Event.objects.filter(pk=obj.pk).update(views_count=F('views_count') + 1)
        obj.views_count += 1

        # Обезличенная статистика по дням (в таблице PageView)
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
                .order_by('-views_count', '-created_at')[:similar_limit - len(similar)]
            )
            similar.extend(fallback)

        context['similar_events'] = similar
        return context