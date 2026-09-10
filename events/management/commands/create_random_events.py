import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from events.models import Event, Category, Place

User = get_user_model()

class Command(BaseCommand):
    help = 'Создает 100 случайных мероприятий'

    def handle(self, *args, **kwargs):
        # Проверяем наличие категорий
        categories = list(Category.objects.all())
        if not categories:
            self.stdout.write(self.style.ERROR('Нет категорий! Создайте хотя бы одну.'))
            return

        # Проверяем наличие площадок
        places = list(Place.objects.all())
        if not places:
            self.stdout.write(self.style.ERROR('Нет площадок! Создайте хотя бы одну.'))
            return

        # Названия для генерации
        event_titles = [
            'Концерт', 'Фестиваль', 'Выставка', 'Мастер-класс', 'Лекция',
            'Спектакль', 'Кинопоказ', 'Вечеринка', 'Ярмарка', 'Конференция',
            'Воркшоп', 'Экскурсия', 'Тренинг', 'Соревнование', 'Презентация',
            'Гастрономический вечер', 'Арт-выставка', 'Джазовый вечер',
            'Рок-концерт', 'Поэтический вечер', 'Танцевальный баттл',
            'Квиз', 'Игровой турнир', 'Благотворительный вечер',
            'Научное шоу', 'Кулинарный мастер-класс', 'Фото-выставка',
            'Театральная постановка', 'Музыкальный фестиваль', 'Стендап',
        ]

        adjectives = [
            'Большой', 'Малый', 'Зимний', 'Летний', 'Осенний', 'Весенний',
            'Ночной', 'Дневной', 'Городской', 'Международный', 'Открытый',
            'Закрытый', 'Юбилейный', 'Первый', 'Ежегодный', 'Специальный',
            'Уникальный', 'Эксклюзивный', 'Традиционный', 'Современный',
            'Классический', 'Авангардный', 'Экспериментальный', 'Премиальный',
        ]

        themes = [
            'искусства', 'музыки', 'кино', 'науки', 'технологий',
            'культуры', 'спорта', 'моды', 'дизайна', 'фотографии',
            'литературы', 'танца', 'театра', 'гастрономии', 'путешествий',
            'экологии', 'образования', 'бизнеса', 'инноваций', 'истории',
        ]

        # Статусы
        statuses = [
            Event.Status.DRAFT,
            Event.Status.MODERATION,
            Event.Status.PUBLISHED,
            Event.Status.CANCELLED,
            Event.Status.FINISHED,
        ]

        # Возрастные ограничения
        age_restrictions = [
            Event.AgeRestriction.ZERO,
            Event.AgeRestriction.SIX,
            Event.AgeRestriction.TWELVE,
            Event.AgeRestriction.SIXTEEN,
            Event.AgeRestriction.EIGHTEEN,
        ]

        # Типы расписания
        schedule_types = [
            Event.ScheduleType.SINGLE,
            Event.ScheduleType.MULTIPLE,
            Event.ScheduleType.RECURRING,
        ]

        events_created = 0

        for i in range(100):
            # Генерируем название
            adjective = random.choice(adjectives)
            title = random.choice(event_titles)
            theme = random.choice(themes)
            
            if random.random() > 0.5:
                event_title = f"{adjective} {title.lower()} {theme}"
            else:
                event_title = f"{title} {theme}"
            
            # Уникальный slug
            base_slug = slugify(event_title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Даты
            start_date = timezone.now().date() + timedelta(days=random.randint(-30, 365))
            
            # Если событие в прошлом, то статус FINISHED
            if start_date < timezone.now().date():
                status = Event.Status.FINISHED
            else:
                status = random.choice(statuses)
            
            # Время
            if random.random() > 0.1:
                start_time = datetime.strptime(
                    f"{random.randint(8, 22)}:{random.choice([0, 15, 30, 45])}", 
                    "%H:%M"
                ).time()
            else:
                start_time = None

            # Цена
            is_free = random.random() < 0.3
            if is_free:
                price = None
            else:
                price = Decimal(random.choice([500, 1000, 1500, 2000, 2500, 3000, 5000]))

            # Описания
            description_short = f"Краткое описание {event_title}. Приходите и узнайте больше!"
            description = f"Полное описание мероприятия {event_title}. "
            description += "Это уникальная возможность погрузиться в атмосферу события. "
            description += "Вас ждет насыщенная программа, интересные гости и незабываемые впечатления. "
            description += "Не упустите шанс стать частью этого события!"

            # Создаем событие
            try:
                event = Event.objects.create(
                    place=random.choice(places),
                    category=random.choice(categories),
                    title=event_title,
                    slug=slug,
                    description_short=description_short[:500],
                    description=description,
                    schedule_type=random.choice(schedule_types),
                    status=status,
                    age_restriction=random.choice(age_restrictions),
                    start_date=start_date,
                    end_date=start_date + timedelta(days=random.randint(0, 7)) if random.random() > 0.5 else None,
                    start_time=start_time,
                    price=price,
                    is_free=is_free,
                    views_count=random.randint(0, 10000),
                    favorites_count=random.randint(0, 1000),
                    contact_email=f"info{random.randint(1, 999)}@example.com",
                    contact_phone=f"+7{random.randint(900, 999)}{random.randint(100, 999)}{random.randint(10, 99)}{random.randint(10, 99)}",
                )
                events_created += 1
                
                if events_created % 20 == 0:
                    self.stdout.write(f'Создано {events_created} мероприятий...')
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Ошибка при создании: {e}'))

        self.stdout.write(
            self.style.SUCCESS(f'Успешно создано {events_created} мероприятий!')
        )