from .base import *


# ================   DEBUG CONFIGURATION
DEBUG = False
TEMPLATE_DEBUG = DEBUG


# ================   project CONFIGURATION
ALLOWED_HOSTS = ['buh.unknownbug.net']


# ================   APP CONFIGURATION
INSTALLED_APPS += [
]


# ================   TEMPLATE CONFIGURATION
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ['django.template.loaders.cached.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader', ], ],
]


# security configuration
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
