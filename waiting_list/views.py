import logging
from datetime import timedelta

from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.conf import settings

from .forms import InterestForm
from .models import InterestResponse

logger = logging.getLogger("waiting_list")


def landing_page(request):
    form = InterestForm()
    total_count = InterestResponse.objects.count()
    return render(
        request,
        "waiting_list/landing.html",
        {"form": form, "total_count": total_count},
    )


def submit_interest(request):
    if request.method != "POST":
        return redirect("waiting_list:landing")

    form = InterestForm(request.POST)

    if not form.is_valid():
        total_count = InterestResponse.objects.count()
        return render(
            request,
            "waiting_list/landing.html",
            {"form": form, "total_count": total_count},
        )

    # Получаем IP
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    # Rate-limit: проверяем, не подписывался ли уже этот IP недавно
    cooldown = getattr(settings, "SUBSCRIBE_COOLDOWN_SECONDS", 30)
    cutoff = timezone.now() - timedelta(seconds=cooldown)
    recent = InterestResponse.objects.filter(
        ip_address=ip,
        created_at__gte=cutoff,
    ).exists()

    if recent:
        logger.warning("Rate-limit: повторная подписка с IP %s", ip)
        messages.warning(
            request,
            "Вы только что подписались. Подождите немного перед следующей попыткой.",
        )
        return redirect("waiting_list:landing")

    # Сохраняем
    try:
        instance = form.save(commit=False)
        instance.ip_address = ip
        instance.save()
        logger.info("Новая подписка: %s (IP: %s)", instance.email, ip)
        messages.success(
            request,
            "Готово! Вы в списке — афиша придёт сразу после запуска.",
        )
    except IntegrityError:
        logger.info("Дубль email: %s", form.cleaned_data.get("email"))
        messages.info(
            request,
            "Вы уже подписаны — спасибо! Афиша придёт сразу после запуска.",
        )

    return redirect("waiting_list:landing")


def robots_txt(request):
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: https://iskitim-afisha.ru/sitemap.xml\n"
    )
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    today = timezone.now().date().isoformat()
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://iskitim-afisha.ru/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    return HttpResponse(content, content_type="application/xml")
