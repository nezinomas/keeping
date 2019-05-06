import os

from django.core.wsgi import get_wsgi_application

from project.config.secrets import get_secret

os.environ["DJANGO_SETTINGS_MODULE"] = get_secret("DJANGO_SETTINGS_MODULE")

application = get_wsgi_application()
