import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

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
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
else:
    SECRET_KEY = os.environ.get(
        "DJANGO_SECRET_KEY",
        "django-insecure-dev-key-change-me-in-production",
    )

_default_hosts = "127.0.0.1,localhost"
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", _default_hosts).split(",")
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]


# =========================================================
# HTTPS / COOKIES — только в проде
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
# ВКЛЮЧЕНИЕ КУКИ И МЕТРИКИ
# Пока не подано уведомление в Роскомнадзор — False.
# После подачи — поставить True в .env и перезапустить gunicorn.
# =========================================================
COOKIES_ENABLED = os.environ.get("COOKIES_ENABLED", "False").lower() in ("1", "true", "yes", "on")
METRIKA_ENABLED = os.environ.get("METRIKA_ENABLED", "False").lower() in ("1", "true", "yes", "on")


# =========================================================
# ПРИЛОЖЕНИЯ
# =========================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",

    "easy_thumbnails",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.vk",
    "django_consent_152fz",
    "django_cookies_152fz",

    'accounts',
    "events",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

DJANGO_CONSENT_152FZ = {"enable_core": True}

DJANGO_COOKIES_152FZ = {
    "enable_cookies": COOKIES_ENABLED,
    "metrika_id": "112359122" if METRIKA_ENABLED else None,
    "consent_ttl_days": 180,
    "privacy_url": "/privacy/",
    "consent_url": "/consent/",
    "anonymize_ip": True,
    "webvisor": True,
}

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
    "allauth.account.middleware.AccountMiddleware",
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
        "DIRS": [os.path.join(BASE_DIR, 'templates')],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "config.context_processors.metrika_context",
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
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
        },
    }
else:
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
LOGIN_URL = "/login/"
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
    "Афиша Искитим <hello@afisha-iskitim.ru>",
)

SERVER_EMAIL = os.environ.get(
    "SERVER_EMAIL",
    "hello@afisha-iskitim.ru",
)

ADMINS = [
    ("Тимофей", "kalinin.timofei@mail.ru"),
]

MANAGERS = ADMINS


# =========================================================
# ЛОГИРОВАНИЕ
# =========================================================
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },

    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
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
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "errors.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "mail_admins": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
    },

    "loggers": {
        "django.request": {
            "handlers": ["console", "error_file", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console", "error_file", "mail_admins"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.template": {
            "handlers": ["console", "error_file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "captcha": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "": {
            "handlers": ["console", "error_file"],
            "level": "WARNING",
            "propagate": True,
        },
    },
}

if IS_PROD:
    LOGGING["handlers"]["console"]["level"] = "WARNING"


# =========================================================
# EASY-THUMBNAILS
# =========================================================
THUMBNAIL_ALIASES = {
    "": {
        "card":    {"size": (600, 800),   "crop": "50%,25%", "quality": 85},
        "card_2x": {"size": (1200, 1600), "crop": "50%,25%", "quality": 80},
        "detail":      {"size": (1200, 1600), "crop": False, "quality": 90},
        "detail_2x":   {"size": (1800, 2400), "crop": False, "quality": 85},
        "gallery":       {"size": (1200, 1200), "crop": "50%,25%", "quality": 85},
        "gallery_2x":    {"size": (1800, 1800), "crop": "50%,25%", "quality": 80},
        "gallery_thumb": {"size": (200, 200),   "crop": "50%,25%", "quality": 80},
        "og": {"size": (1200, 630), "crop": "center", "quality": 85},
        "admin_thumb": {"size": (80, 60), "crop": "center", "quality": 80},
    },
}


THUMBNAIL_OPTIMIZE = True
THUMBNAIL_QUALITY = 85
THUMBNAIL_PRESERVE_EXTENSIONS = ("png",)
THUMBNAIL_HIGH_RESOLUTION = True
THUMBNAIL_EXTENSION = "jpg"


# =========================================================
# СОЦСЕТИ (allauth)
# =========================================================
SOCIALACCOUNT_PROVIDERS = {
    "vk": {
        "APP": {
            "client_id": os.environ.get("VK_CLIENT_ID", "54778776"),
            "secret": os.environ.get("VK_SECRET_KEY", ""),
        },
        "SCOPE": ["email"],
    }
}

ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_ADAPTER = "accounts.adapter.SocialAccountAdapter"

SOCIALACCOUNT_FORMS = {
    'signup': 'accounts.forms.CustomSocialSignupForm',
}


# =========================================================
# YANDEX.METRIKA
# =========================================================
YANDEX_METRIKA_ID = "112359122" if METRIKA_ENABLED else None
