from allauth.account.forms import SignupForm
from django import forms

from .models import ConsentRecord, LegalDocument


class CustomSocialSignupForm(SignupForm):
    """Расширение стандартной формы allauth для VK-регистрации."""
    consent = forms.BooleanField(
        required=True,
        label='',
        widget=forms.CheckboxInput(attrs={'class': 'auth-checkbox'}),
        error_messages={
            'required': 'Необходимо согласие на обработку персональных данных.'
        }
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def save(self, request):
        user = super().save(request)

        # Сохраняем согласие с активной редакцией политики
        privacy_doc = LegalDocument.objects.filter(
            doc_type='privacy', is_active=True
        ).first()
        terms_doc = LegalDocument.objects.filter(
            doc_type='terms', is_active=True
        ).first()

        ip = None
        ua = ''
        if self.request:
            ip = self.request.META.get('HTTP_X_FORWARDED_FOR')
            if ip:
                ip = ip.split(',')[0].strip()
            else:
                ip = self.request.META.get('REMOTE_ADDR')
            ua = self.request.META.get('HTTP_USER_AGENT', '')

        if privacy_doc:
            ConsentRecord.objects.create(
                user=user,
                document=privacy_doc,
                purpose='registration',
                channel='vk-signup',
                ip_address=ip,
                user_agent=ua,
            )
        if terms_doc:
            ConsentRecord.objects.create(
                user=user,
                document=terms_doc,
                purpose='registration',
                channel='vk-signup',
                ip_address=ip,
                user_agent=ua,
            )

        return user
