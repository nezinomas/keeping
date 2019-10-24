from django.apps import AppConfig


class SavingsConfig(AppConfig):
    name = 'project.savings'

    def ready(self):
        from ..core.signals import post_save_account_stats
