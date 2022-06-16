from .base import *

# ================   DEBUG CONFIGURATION
DEBUG = True
TEMPLATE_DEBUG = DEBUG


# ================   project CONFIGURATION
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")


# ================   APP CONFIGURATION
INSTALLED_APPS += [
    'debug_toolbar',
    'django_extensions',
]


STATIC_ROOT = None
STATICFILES_DIRS = [
    os.path.join(SITE_ROOT, 'static'),
]

# print SQL queries in shell_plus
SHELL_PLUS_PRINT_SQL = True


# ================   MIDDLEWARE CONFIGURATION
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # 'pyinstrument.middleware.ProfilerMiddleware',
] + MIDDLEWARE

# PYINSTRUMENT_PROFILE_DIR = 'profiles'

# Overwriten TEMPLATE OPTION
# disabled template cashing
TEMPLATES[0]['OPTIONS']['loaders'] = [
    'django_spaceless_templates.loaders.filesystem.Loader',
    'django_spaceless_templates.loaders.app_directories.Loader', ]


INTERNAL_IPS = ('127.0.0.1', 'localhost', )

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]


DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TEMPLATE_CONTEXT': True,
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    # 'INSERT_BEFORE': '</head>',
}


# ================   DUMMY CASHE
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
