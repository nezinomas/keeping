import os

from django.utils.translation import gettext_lazy as _

from ..secrets import get_secret


AUTH_USER_MODEL = 'users.User'

PROJECT_APPS = [
    'users',
    'accounts',
    'bookkeeping',
    'books',
    'core',
    'counters',
    'debts',
    'drinks',
    'expenses',
    'incomes',
    'journals',
    'counts',
    'savings',
    'pensions',
    'plans',
    'transactions',
]


# ================   PATH CONFIGURATION
# ..\root_catalog\project_catalog\config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ..\root_catalog\project_catalog
SITE_ROOT = os.path.dirname(BASE_DIR)
# ..\project_catalog
PROJECT_ROOT = os.path.dirname(SITE_ROOT)


# ================   SITE CONFIGURATION
LOGOUT_REDIRECT_URL = 'bookkeeping:index'
LOGIN_REDIRECT_URL = 'bookkeeping:index'
LOGIN_URL = 'users:login'


# ================   MEDIA CONFIGURATION
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')
MEDIA_URL = "/media/"


# ================   STATIC FILE CONFIGURATION
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(SITE_ROOT, 'static')


# ================   DEBUG CONFIGURATION
DEBUG = False
TEMPLATE_DEBUG = DEBUG


# ================   SECRET CONFIGURATION
SECRET_KEY = get_secret("SECRET_KEY")


# ================   SITE CONFIGURATION
ALLOWED_HOSTS = ['*']


# ================   DATABASE CONFIGURATION
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': os.path.join(PROJECT_ROOT, '_config_db.cnf'),
        },
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# ================   GENERAL CONFIGURATION
LANGUAGE_CODE = 'lt'

LANGUAGES = [
    ('en', _('English')),
    ('lt', _('Lithuania')),
]
LOCALE_PATHS = [os.path.join(SITE_ROOT, 'locale')]


TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

USE_THOUSAND_SEPARATOR = True

FORMAT_MODULE_PATH = [
    'project.config.formats',
]


# ================   TEMPLATE CONFIGURATION
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(SITE_ROOT, 'templates')],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.static',
                'project.core.context.years',
                'project.core.context.yday',
                'project.core.context.context_months',
            ],
        },
    },
]


# ================   MIDDLEWARE CONFIGURATION
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'crequest.middleware.CrequestMiddleware',
]


SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'


# ================   APP CONFIGURATION
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'bootstrap_datepicker_plus',
    'crispy_forms',
    'crispy_bootstrap5',
    'crequest',
]

for app in PROJECT_APPS:
    INSTALLED_APPS.append(f'project.{app}')


# ================   URL CONFIGURATION
ROOT_URLCONF = 'project.config.urls'


# ================   WSGI CONFIGURATION
WSGI_APPLICATION = 'project.config.wsgi.application'


# ================   PASSWORD VALIDATORS CONFIGURATION
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ================   CRISPY FORMS
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
