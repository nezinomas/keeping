from django.apps import AppConfig

App_name = 'expenses'


class ExpensesConfig(AppConfig):
    name = 'project.expenses'

    def ready(self):
        from ..core.signals import post_save_account_stats
