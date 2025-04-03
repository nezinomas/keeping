#!/usr/bin/env python
import os
import sys
import tomllib as toml
from pathlib import Path

if __name__ == "__main__":
    # Set the project base directory
    conf_file = Path(Path(__file__).cwd(), ".conf")

    # Take environment variables from .conf file
    try:
        conf = conf_file.read_text()
        conf = toml.loads(conf)["django"]

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"File not found: {conf_file}. Please create a .conf file with the required settings."  # noqa: E501
        ) from e

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
