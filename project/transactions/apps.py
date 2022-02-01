from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    name = 'project.transactions'

    def ready(self):
        from ..core.signals import savings_post_signal
