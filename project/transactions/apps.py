from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    name = 'project.transactions'

    def ready(self):
        from ..core.signals import savings_post_save, savings_post_delete
        from ..core.signals import accounts_post_save, accounts_post_delete
