#!/usr/bin/env python
import os
import sys

import environ


if __name__ == "__main__":
    # Set the project base directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Take environment variables from .env file
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

    # set settings file develop/productions/test
    env = environ.Env()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", env("DJANGO_SETTINGS_MODULE"))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
