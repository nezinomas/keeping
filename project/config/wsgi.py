import os

import environ
from django.core.wsgi import get_wsgi_application

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Take environment variables from .env file
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '_config_secrets.env'))


os.environ["DJANGO_SETTINGS_MODULE"] = env("DJANGO_SETTINGS_MODULE")

application = get_wsgi_application()
