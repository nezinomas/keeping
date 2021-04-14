from project.accounts.apps import App_name
from django.apps import AppConfig

App_name = 'plans'
class PlansConfig(AppConfig):
    name = f'project.{App_name}'
