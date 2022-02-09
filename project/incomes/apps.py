from django.apps import AppConfig


class IncomesConfig(AppConfig):
    name = 'project.incomes'

    def ready(self):
        from ..core.signals import accounts_post_save, accounts_post_delete
