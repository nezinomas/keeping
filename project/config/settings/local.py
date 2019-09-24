from .base import *

# ================   DEBUG CONFIGURATION
DEBUG = True
TEMPLATE_DEBUG = DEBUG


# ================   project CONFIGURATION
ALLOWED_HOSTS = ['*']


# ================   APP CONFIGURATION
INSTALLED_APPS += [
    'debug_toolbar',
    'django_extensions',
]


# print SQL queries in shell_plus
SHELL_PLUS_PRINT_SQL = True

# ================   STATIC FILE CONFIGURATION
# STATICFILES_DIRS = [
#     os.path.join(SITE_ROOT, 'static'),
# ]
# STATIC_ROOT = None


# ================   MIDDLEWARE CONFIGURATION
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # 'customizable_django_profiler.cProfileMiddleware',
] + MIDDLEWARE

# PROFILER = {
#     'activate': True,
#     'count': '50',
# }


# ================   DEBUG_TOOLBAR_PANEL
DEBUG_TOOLBAR_PATCH_SETTINGS = False
INTERNAL_IPS = ['127.0.0.1', 'localhost']
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


# ================   DUMMY CASHE
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
