from django import forms
from captcha.fields import CaptchaField
from .models import InterestResponse


class InterestForm(forms.ModelForm):
    captcha = CaptchaField(label='Введите код с картинки')

    class Meta:
        model = InterestResponse
        fields = ['email', 'comment']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'name@example.com',
                'autocomplete': 'email',
                'inputmode': 'email',
                'required': True,
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Что вам интереснее всего? (по желанию)',
                'rows': 3,
            }),
        }
