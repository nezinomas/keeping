import os
import json

from django.core.exceptions import ImproperlyConfigured


class ReadConfigFile:
    def __init__(self, filename='_config_secrets.json'):
        self._filename = filename
        self._secrets = []

    @property
    def get_values(self):
        #  ..\project_project\project\config
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        #  ..\project_project\project
        project_dir = os.path.dirname(base_dir)
        try:
            with open(os.path.join(project_dir, self._filename)) as f:
                self._secrets = json.loads(f.read())
        except FileNotFoundError:
            raise ImproperlyConfigured('Config filename {} not found.'.format(os.path.join(project_dir, self._filename)))

        return self._secrets


secrets = ReadConfigFile()


def get_secret(setting, secrets=secrets.get_values):
    """Get the secret variable or return explicit exception."""
    try:
        return secrets[setting]
    except KeyError:
        error_msg = "Set the {0} environment variable".format(setting)
    raise ImproperlyConfigured(error_msg)
