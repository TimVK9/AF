from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from .models import Event, EventImage


class EventForm(forms.ModelForm):
    """
    Форма создания/редактирования события.

    slug генерируется автоматически в Event.save() — в форме его нет.
    views_count / favorites_count не редактируются вручную.
    """

    start_date = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'class': 'form-input', 'type': 'date'},
        ),
        input_formats=['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'],
        localize=False,
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'class': 'form-input', 'type': 'date'},
        ),
        input_formats=['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'],
        localize=False,
    )
    start_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={'class': 'form-input', 'type': 'time'},
        ),
        input_formats=['%H:%M', '%H:%M:%S'],
        localize=False,
    )
    end_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={'class': 'form-input', 'type': 'time'},
        ),
        input_formats=['%H:%M', '%H:%M:%S'],
        localize=False,
    )

    class Meta:
        model = Event
        fields = [
            'title',
            'category',
            'place',
            'description_short',
            'description',
            'schedule_type',
            'status',
            'age_restriction',
            'start_date',
            'end_date',
            'start_time',
            'end_time',
            'is_free',
            'price',
            'main_image',
            'contact_email',
            'contact_phone',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Например: Концерт группы «Кино»',
                'autofocus': True,
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'place': forms.Select(attrs={'class': 'form-select'}),
            'description_short': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Одно предложение — оно попадёт в карточку и OG-описание',
                'maxlength': 500,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 12,
                'placeholder': 'Полное описание. Можно использовать пустые строки между абзацами.',
            }),
            'schedule_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'age_restriction': forms.Select(attrs={'class': 'form-select'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'inputmode': 'decimal',
            }),
            'main_image': forms.ClearableFileInput(attrs={
                'class': 'form-file',
                'accept': 'image/*',
            }),
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'email@example.com',
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+7 (999) 123-45-67',
                'inputmode': 'tel',
            }),
        }
        labels = {
            'title': 'Название',
            'category': 'Категория',
            'place': 'Площадка',
            'description_short': 'Краткое описание',
            'description': 'Полное описание',
            'schedule_type': 'Тип расписания',
            'status': 'Статус',
            'age_restriction': 'Возрастное ограничение',
            'start_date': 'Дата начала',
            'end_date': 'Дата окончания',
            'start_time': 'Время начала',
            'end_time': 'Время окончания',
            'is_free': 'Бесплатное событие',
            'price': 'Цена, ₽',
            'main_image': 'Главное изображение',
            'contact_email': 'Email для связи',
            'contact_phone': 'Телефон для связи',
        }
        help_texts = {
            'title': 'От 5 до 200 символов. По нему генерируется URL.',
            'category': 'Определяет раздел афиши и цвет бейджа.',
            'place': 'Если нужной площадки нет — создайте её в админке.',
            'description_short': 'До 500 символов. Показывается в карточке и в соцсетях.',
            'description': 'Полный текст страницы. Поддерживаются переносы строк.',
            'schedule_type': 'Однократное — концерт, многократное — выставка, повторяющееся — курс.',
            'status': '«Черновик» и «На модерации» не показываются в афише.',
            'age_restriction': 'Влияет на бейдж в карточке и Schema.org.',
            'start_date': 'Обязательное поле.',
            'end_date': 'Оставьте пустым для однодневного события.',
            'start_time': 'Можно не указывать, если время не важно.',
            'end_time': 'Только если есть start_time.',
            'is_free': 'Если отмечено — цена сбрасывается.',
            'price': 'В рублях. Можно оставить пустым, если цена «уточняется».',
            'main_image': 'JPEG/PNG, желательно 1200×630 или больше. Если не задано — используется фото площадки.',
            'contact_email': 'Необязательно. Появится на странице события.',
            'contact_phone': 'Необязательно. Появится на странице события.',
        }

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if len(title) < 5:
            raise ValidationError('Название должно быть не короче 5 символов.')
        return title

    def clean(self):
        cleaned = super().clean()

        start_date = cleaned.get('start_date')
        end_date = cleaned.get('end_date')
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')
        is_free = cleaned.get('is_free')
        price = cleaned.get('price')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', 'Дата окончания не может быть раньше даты начала.')

        if (
            start_date and end_date and start_date == end_date
            and start_time and end_time and end_time < start_time
        ):
            self.add_error('end_time', 'Время окончания не может быть раньше времени начала.')

        if end_time and not start_time:
            self.add_error('end_time', 'Укажите время начала, прежде чем задавать время окончания.')

        if is_free and price:
            self.add_error('price', 'У бесплатного события не может быть цены. Снимите галочку «Бесплатное» или очистите цену.')

        return cleaned


class EventImageForm(forms.ModelForm):
    """Дополнительное изображение галереи."""

    class Meta:
        model = EventImage
        fields = ['image', 'caption', 'order']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-file',
                'accept': 'image/*',
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Подпись к фото (необязательно)',
                'maxlength': 200,
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': '0',
                'inputmode': 'numeric',
            }),
        }
        labels = {
            'image': 'Изображение',
            'caption': 'Подпись',
            'order': 'Порядок',
        }


EventImageFormSet = forms.inlineformset_factory(
    Event,
    EventImage,
    form=EventImageForm,
    extra=3,
    can_delete=True,
    max_num=15,
)