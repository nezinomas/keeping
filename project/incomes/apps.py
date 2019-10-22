from django.apps import AppConfig


class IncomesConfig(AppConfig):
    name = 'incomes'

    def ready(self):
        from ..core.signals import post_save_account_stats
