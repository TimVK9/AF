"""Аутентификация: вход по логину/паролю + 2FA через email-код."""
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .models import EmailOTP


SESSION_KEY_USER_ID = 'pre_2fa_user_id'
SESSION_KEY_REMEMBER = 'pre_2fa_remember'


def login_view(request):
    """
    Первый шаг входа: логин + пароль.
    При успехе создаёт код, шлёт на email, редиректит на /verify/.
    """
    if request.user.is_authenticated:
        return redirect('events:home')

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        remember = request.POST.get('remember') == 'on'

        user = authenticate(request, username=username, password=password)
        if user is None:
            messages.error(request, 'Неверный логин или пароль.')
        elif not user.is_active:
            messages.error(request, 'Учётная запись отключена.')
        else:
            otp = EmailOTP.issue(user)
            _send_otp_email(user, otp)

            request.session[SESSION_KEY_USER_ID] = user.pk
            request.session[SESSION_KEY_REMEMBER] = remember
            return redirect('accounts:verify')

    return render(request, 'accounts/auth/login.html')


def verify_view(request):
    """Второй шаг входа: ввод кода из письма."""
    user_id = request.session.get(SESSION_KEY_USER_ID)
    if not user_id:
        return redirect('accounts:login')

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('accounts:login')

    if request.method == 'POST':
        raw_code = (request.POST.get('code') or '').strip()
        otp = (
            EmailOTP.objects
            .filter(user=user, is_used=False)
            .order_by('-created_at')
            .first()
        )

        if otp is None:
            messages.error(request, 'Код не найден. Запросите новый.')
        elif otp.is_expired:
            messages.error(request, 'Код истёк. Запросите новый.')
        elif not otp.matches(raw_code):
            messages.error(request, 'Неверный код.')
        else:
            otp.is_used = True
            otp.save(update_fields=['is_used'])

            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            if not request.session.get(SESSION_KEY_REMEMBER):
                request.session.set_expiry(0)

            request.session.pop(SESSION_KEY_USER_ID, None)
            request.session.pop(SESSION_KEY_REMEMBER, None)
            return redirect('events:home')

    return render(request, 'accounts/auth/verify.html')


def resend_otp_view(request):
    """Повторная отправка кода."""
    user_id = request.session.get(SESSION_KEY_USER_ID)
    if not user_id:
        return redirect('accounts:login')

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('accounts:login')

    otp = EmailOTP.issue(user)
    _send_otp_email(user, otp)
    messages.success(request, 'Новый код отправлен на почту.')
    return redirect('accounts:verify')


@require_POST
def logout_view(request):
    logout(request)
    return redirect('events:home')


def _send_otp_email(user, otp):
    """Отправка кода на email пользователя — HTML + текстовый fallback."""
    email = (user.email or '').strip()
    if not email:
        print(f'[2FA] Пользователь {user.username} без email. Код: {otp.code}')
        return

    context = {
        'code': otp.code,
        'name': user.get_short_name() or user.username,
    }

    html_body = render_to_string('accounts/emails/otp.html', context)
    text_body = render_to_string('accounts/emails/otp.txt', context)

    send_mail(
        subject='Код подтверждения входа — Афиша Искитим',
        message=text_body,
        from_email=None,
        recipient_list=[email],
        html_message=html_body,
        fail_silently=False,
    )
