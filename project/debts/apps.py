from django.apps import AppConfig

App_name = 'debts'

class DebtsConfig(AppConfig):
    name = f'project.{App_name}'

    def ready(self):
        from ..core.signals import accounts_post_signal
