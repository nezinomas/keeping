import os

import tomllib
from django.core.wsgi import get_wsgi_application

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Take environment variables from .conf file
with open(os.path.join(BASE_DIR, '.conf'), "rb") as f:
    conf = tomllib.load(f)["django"]


os.environ["DJANGO_SETTINGS_MODULE"] = conf["DJANGO_SETTINGS_MODULE"]

application = get_wsgi_application()
