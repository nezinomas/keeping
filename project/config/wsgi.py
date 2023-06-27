import os
from pathlib import Path

import tomllib as toml
from django.core.wsgi import get_wsgi_application


# Set the project base directory
BASE_DIR = Path().cwd()

# Take environment variables from .conf file
with open(BASE_DIR / ".conf", "rb") as f:
    conf = toml.load(f)["django"]

os.environ["DJANGO_SETTINGS_MODULE"] = conf["DJANGO_SETTINGS_MODULE"]

application = get_wsgi_application()
