from django.apps import AppConfig

from project.accounts.apps import App_name

App_name = "plans"


class PlansConfig(AppConfig):
    name = f"project.{App_name}"
