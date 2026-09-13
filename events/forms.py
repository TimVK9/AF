from django import forms
from django.core.exceptions import ValidationError

from .models import Event, EventImage


class EventForm(forms.ModelForm):
    """Форма создания/редактирования события."""

    # ------------------------------------------------------------------
    # Явные поля для <input type="date"> и <input type="time">
    # format — как рендерить значение, input_formats — что принимать,
    # localize=False — отключить локализацию (иначе Django даст 15.09.2026).
    # ------------------------------------------------------------------
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
            'organizer_name',
            'organizer_email',
            'organizer_phone',
            'organizer_vk',
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
            'organizer_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Например: ДК «Молодость»',
            }),
            'organizer_email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'org@example.com',
            }),
            'organizer_phone': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+7 (999) 123-45-67',
                'inputmode': 'tel',
            }),
            'organizer_vk': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://vk.com/club12345',
                'inputmode': 'url',
            }),
            # ВАЖНО: start_date / end_date / start_time / end_time
            # НЕ указываются здесь — они уже заданы явными полями выше.
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
            'organizer_name': 'Организатор',
            'organizer_email': 'Email организатора',
            'organizer_phone': 'Телефон организатора',
            'organizer_vk': 'ВКонтакте',
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
            'organizer_name': 'Название организации или имя — появится в карточке события.',
            'organizer_email': 'Необязательно. Показывается на странице события.',
            'organizer_phone': 'Необязательно. Показывается на странице события.',
            'organizer_vk': 'Полная ссылка на страницу или сообщество, например https://vk.com/club12345.',
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