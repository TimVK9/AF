from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone
from tours.models import TourEvent, TourVenue

def iskitim_events(request):
    # Показываем только активные события
    qs = TourEvent.objects.filter(is_active=True, is_published=True)

    # Опционально: фильтр по дате (?date=2026-10-01)
    date_param = request.GET.get('date')
    if date_param:
        qs = qs.filter(start_date=date_param)
    else:
        # По умолчанию — события от сегодня и дальше
        qs = qs.filter(start_date__gte=timezone.now().date())

    # Сортировка по дате
    qs = qs.order_by('start_date', 'start_time')

    context = {
        'events': qs,
        'today': timezone.now().date(),
    }
    return render(request, 'tours/iskitim_events.html', context)
