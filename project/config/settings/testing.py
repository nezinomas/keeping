from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'


MIGRATION_MODULES = {
    'auth': None,
    'contenttypes': None,
    'default': None,
    'sessions': None,

    'auths': None,
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
