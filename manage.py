#!/usr/bin/env python
import os
import sys

import tomllib


if __name__ == "__main__":
    # Set the project base directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Take environment variables from .conf file
    with open(os.path.join(BASE_DIR, '.conf'), "rb") as f:
        conf = tomllib.load(f)["django"]

    # set settings file develop/productions/test
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", conf["DJANGO_SETTINGS_MODULE"])

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
