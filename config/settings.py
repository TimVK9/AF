"""
Django settings — базовый файл для разработки.

ПРОДАКШЕН: используйте config/settings_prod.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем .env до всех os.environ.get(...)
load_dotenv(BASE_DIR / ".env")


# =========================================================
# БЕЗОПАСНОСТЬ
# =========================================================
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-key-change-me-in-production",
)

DEBUG = True  # ← в этом файле всегда True, для продакшена — settings_prod.py

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if h.strip()
]


# =========================================================
# ПРИЛОЖЕНИЯ
# =========================================================
INSTALLED_APPS = [
        "jazzmin",              # перед django.contrib.admin

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",

    "easy_thumbnails",        

    "events",
     "pages", 
]

SITE_ID = 1


# =========================================================
# MIDDLEWARE
# =========================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================================================
# URLS / WSGI
# =========================================================
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"


# =========================================================
# ШАБЛОНЫ
# =========================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
            ],
        },
    },
]


# =========================================================
# БАЗА ДАННЫХ (SQLite для разработки)
# =========================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# =========================================================
# ПАРОЛИ
# =========================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =========================================================
# ЯЗЫК / ВРЕМЯ
# =========================================================
LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "Asia/Novosibirsk"
USE_I18N = True
USE_TZ = True


# =========================================================
# СТАТИКА / МЕДИА
# =========================================================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# В разработке — обычная отдача файлов
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# =========================================================
# АВТОРИЗАЦИЯ
# =========================================================
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================================================
# БИЗНЕС-ЛОГИКА
# =========================================================
SUBSCRIBE_COOLDOWN_SECONDS = int(
    os.environ.get("SUBSCRIBE_COOLDOWN_SECONDS", "30")
)


# =========================================================
# EMAIL (в разработке — в консоль)
# =========================================================
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Афиша Искитим <hello@iskitim-afisha.ru>",
)


# =========================================================
# ЛОГИРОВАНИЕ
# =========================================================
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "app.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "errors.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "waiting_list": {"handlers": ["console", "file"], "level": "INFO", "propagate": False},
        "captcha": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "": {"handlers": ["console", "error_file"], "level": "WARNING", "propagate": True},
    },
}

# =========================================================
# JAZZMIN — основные настройки
# =========================================================
JAZZMIN_SETTINGS = {
    # Заголовки
    "site_title": "Афиша Искитим — админка",
    "site_header": "Афиша Искитим",
    "site_brand": "АФИШАИСКИТИМ",
    "site_logo": None,                    # можно указать путь к логотипу
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "dashboard_callback": "events.admin.admin_dashboard_callback",

    # Приветствие на странице логина
    "welcome_sign": "Добро пожаловать в панель управления",
    "copyright": "Афиша Искитим",

    # Поиск в хедере
    "search_model": ["events.Event", "events.Place", "events.Category"],

    # Аватар пользователя (поле в User) — у нас его нет, оставляем None
    "user_avatar": None,

    # Верхнее меню
    "topmenu_links": [
        {
            "name": "На сайт",
            "url": "/",
            "new_window": True,
            "icon": "fas fa-external-link-alt",
        },
        {
            "name": "События",
            "model": "events.Event",
            "icon": "fas fa-calendar-alt",
            "permissions": ["events.view_event"],
        },
        {
            "name": "Площадки",
            "model": "events.Place",
            "icon": "fas fa-map-marker-alt",
            "permissions": ["events.view_place"],
        },
        {
            "name": "Помощь",
            "url": "/admin/help/",
            "new_window": True,
            "icon": "fas fa-question-circle",
        },
    ],

    # Правая часть хедера
    "usermenu_links": [
        {
            "name": "На сайт",
            "url": "/",
            "new_window": True,
            "icon": "fas fa-external-link-alt",
        },
    ],

    # Сайдбар
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

    # Кастомный порядок приложений и моделей в сайдбаре
    "order_with_respect_to": [
        "events",
        "events.Event",
        "events.Place",
        "events.Category",
        "events.Address",
        "auth",
        "auth.User",
        "auth.Group",
        "sites",
        "sitemaps",
    ],

    # Иконки
    "icons": {
        # Приложения
        "auth": "fas fa-users-cog",
        "events": "fas fa-calendar-alt",
        "sites": "fas fa-globe",
        "sitemaps": "fas fa-sitemap",

        # Модели
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
        "events.Event": "fas fa-calendar-alt",
        "events.Place": "fas fa-map-marker-alt",
        "events.Category": "fas fa-tags",
        "events.Address": "fas fa-location-arrow",
    },

    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    # Модальные окна для связанных объектов (у нас не будем)
    "related_modal_active": False,

    # Кастомные CSS и JS
    "custom_css": "admin/css/jazzmin_custom.css",
    "custom_js": "admin/js/jazzmin_custom.js",

    # Шрифты
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,

    # Формат форм: "horizontal_tabs" — табы по fieldsets
    "changeform_format": "horizontal_tabs",

    # Переопределяем формат для отдельных моделей
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
        "events.Event": "horizontal_tabs",
    },

    # Язык
    "language_chooser": False,
}

# =========================================================
# JAZZMIN — UI-настройки (цвета, кнопки)
# =========================================================
JAZZMIN_UI_TWEAKS = {
    # Размеры шрифтов
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,

    # Цвета
    "brand_colour": "navbar-success",       # изумрудный хедер
    "accent": "accent-success",             # изумрудные акценты (галочки, radio)
    "navbar": "navbar-dark",                # тёмный текст на светлом фоне (при navbar-success текст белый)
    "no_navbar_border": True,
    "navbar_fixed": True,                   # хедер всегда сверху

    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,                  # сайдбар зафиксирован

    "sidebar": "sidebar-dark-success",      # тёмно-изумрудный сайдбар
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,       # отступы вложенных пунктов
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,

    # Тема
    "theme": "default",
    "dark_mode_theme": "darkly",            # тема для тёмного режима

    # Классы кнопок
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}


# =========================================================
# EASY-THUMBNAILS — оптимизация изображений
# =========================================================
THUMBNAIL_ALIASES = {
    "": {
        # Карточка события на главной
        "card": {"size": (600, 400), "crop": "smart", "quality": 85},

        # Карточка 2x (для Retina)
        "card_2x": {"size": (1200, 800), "crop": "smart", "quality": 80},

        # Главное фото на детальной
        "detail": {"size": (1200, 750), "crop": "smart", "quality": 85},

        # Галерея — большое фото
        "gallery": {"size": (1200, 750), "crop": "smart", "quality": 85},

        # Галерея — миниатюра
        "gallery_thumb": {"size": (200, 150), "crop": "smart", "quality": 80},

        # Превью для админки
        "admin_thumb": {"size": (80, 60), "crop": "smart", "quality": 80},
    },
}

# Оптимизация размера файлов
THUMBNAIL_OPTIMIZE = True
THUMBNAIL_QUALITY = 85
THUMBNAIL_PRESERVE_EXTENSIONS = ("png",)
THUMBNAIL_HIGH_RESOLUTION = True
THUMBNAIL_EXTENSION = "webp"