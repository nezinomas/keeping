from django.apps import AppConfig


class bookkeepingConfig(AppConfig):
    name = 'project.bookkeeping'

    def ready(self):
        from ..core.signals import post_save_account_stats
