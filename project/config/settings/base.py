from pathlib import Path

import tomllib as toml
from django.utils.translation import gettext_lazy as _


PROJECT_APPS = [
    "users",
    "accounts",
    "bookkeeping",
    "books",
    "core",
    "debts",
    "drinks",
    "expenses",
    "incomes",
    "journals",
    "counts",
    "savings",
    "pensions",
    "plans",
    "transactions",
]


AUTH_USER_MODEL = "users.User"

BASE_DIR = Path(__file__).absolute()
PROJECT_ROOT = BASE_DIR.parent.parent.parent.parent
SITE_ROOT = BASE_DIR.parent.parent.parent

print(f'baes.py: {PROJECT_ROOT=} {SITE_ROOT=}')
# Take environment variables from .conf file
with open(PROJECT_ROOT / ".conf", "rb") as f:
    toml = toml.load(f)

    ENV = toml["django"]
    DB = toml["database"]


LOGOUT_REDIRECT_URL = "bookkeeping:index"
LOGIN_REDIRECT_URL = "bookkeeping:index"
LOGIN_URL = "users:login"


MEDIA_ROOT = ENV["MEDIA_ROOT"]
MEDIA_URL = "/media/"


STATIC_URL = "/static/"
STATIC_ROOT = SITE_ROOT / "static"


DEBUG = False
TEMPLATE_DEBUG = DEBUG


SECRET_KEY = ENV["SECRET_KEY"]
SALT = ENV["SALT"]


ALLOWED_HOSTS = []


DATABASES = {"default": DB}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", _("English")),
    ("lt", _("Lithuanian")),
]
LOCALE_PATHS = [SITE_ROOT / "locale"]


TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [SITE_ROOT / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.static",
                "project.core.context.years",
                "project.core.context.yday",
                "project.core.context.context_months",
                "project.core.context.context_counts_menu",
            ],
        },
    },
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "crequest.middleware.CrequestMiddleware",
]


SESSION_SERIALIZER = "django.contrib.sessions.serializers.JSONSerializer"


INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "bootstrap_datepicker_plus",
    "crispy_forms",
    "crispy_bootstrap5",
    "crequest",
    "slippers",
    "django_htmx",
    "widget_tweaks",
]
INSTALLED_APPS.extend(f"project.{app}" for app in PROJECT_APPS)


ROOT_URLCONF = "project.config.urls"


WSGI_APPLICATION = "project.config.wsgi.application"


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


BOOTSTRAP_DATEPICKER_PLUS = {
    "variant_options": {
        "date": {
            "format": "YYYY-MM-DD",
        },
        "year": {
            "format": "YYYY",
        },
    }
}
