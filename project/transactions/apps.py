from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    name = 'project.transactions'

    def ready(self):
        from ..core.signals import accounts_signal, savings_signal
