"""
Django settings — единый файл для dev и prod.

Режим определяется переменной окружения DJANGO_DEBUG:
  - DJANGO_DEBUG=True  (или не задана) → режим разработки
  - DJANGO_DEBUG=False                  → продакшен

Все значения читаются из .env в корне проекта (см. load_dotenv ниже).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# .env читаем ДО любого os.environ.get(...)
load_dotenv(BASE_DIR / ".env")


# =========================================================
# РЕЖИМ
# =========================================================
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes", "on")
IS_PROD = not DEBUG


# =========================================================
# БЕЗОПАСНОСТЬ
# =========================================================
if IS_PROD:
    # В проде SECRET_KEY обязателен, без фоллбэка.
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
else:
    # В dev — мягкий фоллбэк, чтобы можно было запускать без .env.
    SECRET_KEY = os.environ.get(
        "DJANGO_SECRET_KEY",
        "django-insecure-dev-key-change-me-in-production",
    )


# ALLOWED_HOSTS: в проде — из .env, в dev — локальные
_default_hosts = "127.0.0.1,localhost"
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", _default_hosts).split(",")
    if h.strip()
]

# CSRF_TRUSTED_ORIGINS нужен за https-прокси (nginx) в проде.
# В dev, если не задано, оставляем пустым.
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]


# =========================================================
# HTTPS / COOKIES — включаем только в проде
# =========================================================
if IS_PROD:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False

    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"


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
    # 'pages.middleware.ComingSoonMiddleware',  # ← добавить

]

SITE_COMING_SOON = True

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
# БАЗА ДАННЫХ — SQLite
# =========================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            # Ждать до 20 сек при блокировке, а не падать сразу с "database is locked"
            "timeout": 20,
        },
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

if IS_PROD:
    # В проде — хешированные имена файлов (кеш браузера не залипает после деплоя)
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
        },
    }
else:
    # В dev — обычная отдача без манифеста
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
# EMAIL
# =========================================================
# В dev — в консоль, в prod — реальный SMTP.
if IS_PROD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
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

if IS_PROD:
    # В проде console уходит в journald — делаем его потише,
    # подробности всё равно пишутся в файлы.
    LOGGING["handlers"]["console"]["level"] = "WARNING"


# =========================================================
# JAZZMIN — основные настройки
# =========================================================
JAZZMIN_SETTINGS = {
    "site_title": "Афиша Искитим — админка",
    "site_header": "Афиша Искитим",
    "site_brand": "АФИШАИСКИТИМ",
    "site_logo": None,
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,
    "dashboard_callback": "events.admin.admin_dashboard_callback",

    "welcome_sign": "Добро пожаловать в панель управления",
    "copyright": "Афиша Искитим",

    "search_model": ["events.Event", "events.Place", "events.Category"],

    "user_avatar": None,

    "topmenu_links": [
        {"name": "На сайт", "url": "/", "new_window": True, "icon": "fas fa-external-link-alt"},
        {"name": "События", "model": "events.Event", "icon": "fas fa-calendar-alt", "permissions": ["events.view_event"]},
        {"name": "Площадки", "model": "events.Place", "icon": "fas fa-map-marker-alt", "permissions": ["events.view_place"]},
        {"name": "Помощь", "url": "/admin/help/", "new_window": True, "icon": "fas fa-question-circle"},
    ],

    "usermenu_links": [
        {"name": "На сайт", "url": "/", "new_window": True, "icon": "fas fa-external-link-alt"},
    ],

    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],

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

    "icons": {
        "auth": "fas fa-users-cog",
        "events": "fas fa-calendar-alt",
        "sites": "fas fa-globe",
        "sitemaps": "fas fa-sitemap",

        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
        "events.Event": "fas fa-calendar-alt",
        "events.Place": "fas fa-map-marker-alt",
        "events.Category": "fas fa-tags",
        "events.Address": "fas fa-location-arrow",
    },

    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    "related_modal_active": False,

    "custom_css": "admin/css/jazzmin_custom.css",
    "custom_js": "admin/js/jazzmin_custom.js",

    "use_google_fonts_cdn": True,
    "show_ui_builder": False,

    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
        "events.Event": "horizontal_tabs",
    },

    "language_chooser": False,
}


# =========================================================
# JAZZMIN — UI
# =========================================================
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,

    "brand_colour": "navbar-success",
    "accent": "accent-success",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,

    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,

    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,

    "theme": "default",
    "dark_mode_theme": "darkly",

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
# EASY-THUMBNAILS
# =========================================================
THUMBNAIL_ALIASES = {
    "": {
        "card": {"size": (600, 400), "crop": "smart", "quality": 85},
        "card_2x": {"size": (1200, 800), "crop": "smart", "quality": 80},
        "detail": {"size": (1200, 750), "crop": "smart", "quality": 85},
        "gallery": {"size": (1200, 750), "crop": "smart", "quality": 85},
        "gallery_thumb": {"size": (200, 150), "crop": "smart", "quality": 80},
        "admin_thumb": {"size": (80, 60), "crop": "smart", "quality": 80},
    },
}

THUMBNAIL_OPTIMIZE = True
THUMBNAIL_QUALITY = 85
THUMBNAIL_PRESERVE_EXTENSIONS = ("png",)
THUMBNAIL_HIGH_RESOLUTION = True
THUMBNAIL_EXTENSION = "webp"