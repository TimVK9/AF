# Афиша Искитим

Сайт-афиша мероприятий города Искитим.

## Установка

1. Клонировать репозиторий
2. Создать виртуальное окружение: `python -m venv .venv`
3. Активировать: `.venv\Scripts\activate` (Windows) или `source .venv/bin/activate` (Linux/macOS)
4. Установить зависимости: `pip install -r requirements.txt`
5. Создать `.env` на основе `.env.example`
6. Применить миграции: `python manage.py migrate`
7. Создать суперпользователя: `python manage.py createsuperuser`
8. Запустить: `python manage.py runserver`

## Разработка

- Базовые настройки: `config/settings.py` (DEBUG=True, SQLite)
- Продакшен: `config/settings_prod.py`
- `.env` — секреты, не коммитится

## Деплой

См. `DEPLOY.md`.