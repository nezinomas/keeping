from django.apps import AppConfig
from django.db.models.signals import post_save

App_name = "expenses"


class ExpensesConfig(AppConfig):
    name = "project.expenses"

    def ready(self):
        from ..core.signals import (
            accounts_signal,
            connect_save_and_delete,
            update_journal_first_record,
        )
        from .models import Expense

        connect_save_and_delete(accounts_signal, Expense)
        post_save.connect(update_journal_first_record, sender=Expense)
