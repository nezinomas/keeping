from django.apps import AppConfig


class SavingsConfig(AppConfig):
    name = 'project.savings'

    def ready(self):
        from ..core.signals import accounts_signal, savings_signal
