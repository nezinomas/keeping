from django.apps import AppConfig

App_name = "expenses"


class ExpensesConfig(AppConfig):
    name = "project.expenses"

    def ready(self):
        from ..core.signals import accounts_signal, update_journal_first_record
