from project.accounts.apps import App_name
from django.apps import AppConfig

App_name = 'core'

class CoreConfig(AppConfig):
    name = f'project.{App_name}'
