import os
import tomllib as toml
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Set the project base directory
BASE_DIR = Path(__file__).absolute().parent.parent.parent

# Take environment variables from .conf file
with open(BASE_DIR / ".conf", "rb") as f:
    conf = toml.load(f)["django"]

os.environ["DJANGO_SETTINGS_MODULE"] = conf["DJANGO_SETTINGS_MODULE"]

application = get_wsgi_application()
