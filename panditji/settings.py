import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DEBUG = os.getenv("DEBUG", "true").lower() in {"1", "true", "yes"}
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY when DEBUG is false.")
    SECRET_KEY = "django-insecure-local-development-key"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app.apps.BookingsConfig",
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

ROOT_URLCONF = "panditji.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "panditji.wsgi.application"
ASGI_APPLICATION = "panditji.asgi.application"


def database_config():
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data/pandit_ji.db'}")
    parsed = urlsplit(database_url)

    if parsed.scheme.startswith("mysql"):
        return {
            "ENGINE": "django.db.backends.mysql",
            "NAME": unquote(parsed.path.lstrip("/")),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or 3306),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    if parsed.scheme == "sqlite":
        if parsed.path in {"/:memory:", ":memory:"}:
            name = ":memory:"
        else:
            sqlite_path = unquote(parsed.path)
            if sqlite_path.startswith("//"):
                sqlite_path = sqlite_path[1:]
            elif sqlite_path.startswith("/"):
                sqlite_path = sqlite_path[1:]
            name = Path(sqlite_path).expanduser()
            if not name.is_absolute():
                name = (BASE_DIR / name).resolve()
            name.parent.mkdir(parents=True, exist_ok=True)
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": name}
    raise ValueError("DATABASE_URL must use sqlite:// or mysql://")


DATABASES = {"default": database_config()}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = (os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER", "")).strip()
try:
    EMAIL_PORT = int(os.getenv("SMTP_PORT", "587"))
except ValueError:
    EMAIL_PORT = 0
EMAIL_HOST_USER = os.getenv("SMTP_USERNAME", "").strip()
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = (
    os.getenv("SMTP_FROM_EMAIL") or os.getenv("SMTP_FROM", "")
).strip()
BOOKING_ADMIN_EMAIL = (
    os.getenv("ADMIN_EMAIL") or EMAIL_HOST_USER
).strip()
EMAIL_TIMEOUT = 15

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
X_FRAME_OPTIONS = "DENY"
