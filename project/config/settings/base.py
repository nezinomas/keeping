import os
from ..secrets import get_secret

# ================   PATH CONFIGURATION
# ..\root_catalog\project_catalog\config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ..\root_catalog\project_catalog
SITE_ROOT = os.path.dirname(BASE_DIR)
# ..\procect_catalog
PROJECT_ROOT = os.path.dirname(SITE_ROOT)


# ================   SITE CONFIGURATION
LOGOUT_REDIRECT_URL = 'bookkeeping:index'
LOGIN_REDIRECT_URL = 'bookkeeping:index'
LOGIN_URL = 'auths:login'


# ================   MEDIA CONFIGURATION
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')
MEDIA_URL = "/media/"


# ================   STATIC FILE CONFIGURATION
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(SITE_ROOT, 'static'),
]
# STATIC_ROOT = os.path.join(SITE_ROOT, 'static')


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


# ================   GENERAL CONFIGURATION
LANGUAGE_CODE = 'lt'
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
        'DIRS': [os.path.join(project_ROOT, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
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
]


# ================   APP CONFIGURATION
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'bootstrap_datepicker_plus',
    'widget_tweaks',
    'crispy_forms',
    'bootstrap4',
    'project.auths',
    'project.accounts',
    'project.bookkeeping',
    'project.books',
    'project.core',
    'project.drinks',
    'project.expenses',
    'project.incomes',
    'project.savings',
    'project.plans',
    'project.transactions',
]


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
CRISPY_TEMPLATE_PACK = 'bootstrap4'
