import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# В продакшене SECRET_KEY и DEBUG берутся из переменных окружения
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-4txo7qx&7ghsq0^6=^$ti8e@w3fr$ee@lm9db_a0=tkuiatxu&",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS",
    "iskitim-afisha.ru,www.iskitim-afisha.ru,127.0.0.1,localhost",
).split(",")

SITE_ID = 1

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "captcha",
    "waiting_list",
]

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

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Novosibirsk"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Простой rate-limit: сколько секунд между подписками с одного IP
SUBSCRIBE_COOLDOWN_SECONDS = 30

# ---------------------------------------------------------
# EMAIL (рассылка)
# ---------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "hello@iskitim-afisha.ru"
)

# ---------------------------------------------------------
# БЕЗОПАСНОСТЬ (только для продакшена, DEBUG=False)
# ---------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------------------------------------------
# ЛОГИРОВАНИЕ
# ---------------------------------------------------------
LOGS_DIR = BASE_DIR / "logs"
if DEBUG:
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
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "app.log" if LOGS_DIR.exists() else None,
            "formatter": "verbose",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "errors.log" if LOGS_DIR.exists() else None,
            "formatter": "verbose",
        },
    },
    "loggers": {
        "waiting_list": {
            "handlers": ["console", "file"] if DEBUG else ["console"],
            "level": "INFO",
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
            "handlers": ["console", "error_file"] if DEBUG else ["console"],
            "level": "WARNING",
            "propagate": True,
        },
    },
}

# WhiteNoise: сжатие статики
STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
    if not DEBUG
    else "django.contrib.staticfiles.storage.StaticFilesStorage"
)
