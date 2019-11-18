from .base import *

DEBUG = False


TEMPLATES[0]['OPTIONS']['debug'] = False


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': ''
    }
}


TEMPLATES[0]['OPTIONS']['loaders'] = [
    ['django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader', ], ],
]


MIGRATION_MODULES = {
    'auth': None,
    'contenttypes': None,
    'default': None,
    'sessions': None,

    'users': None,
    'accounts': None,
    'bookkeeping': None,
    'books': None,
    'core': None,
    'drinks': None,
    'expenses': None,
    'incomes': None,
    'savings': None,
    'plans': None,
    'transactions': None
}
