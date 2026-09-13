"""
Служебные вью для админки: запуск парсера kultisk.ru.
"""

import re
from io import StringIO

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import ImportLog, Event


@staff_member_required
def run_import_kultisk(request):
    """
    GET  — показывает страницу с кнопкой подтверждения.
    POST — запускает команду и сохраняет результат в ImportLog.
    """
    if request.method == 'POST':
        return _run_import(request)

    moderation_count = Event.objects.filter(
        status=Event.Status.MODERATION
    ).count()

    last_logs = (
        ImportLog.objects
        .filter(source=ImportLog.Source.KULTISK)
        .select_related('created_by')[:5]
    )

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
    """Достаёт первое число после 'prefix' из текста."""
    m = re.search(rf'{re.escape(prefix)}\s*(\d+)', text)
    return int(m.group(1)) if m else 0