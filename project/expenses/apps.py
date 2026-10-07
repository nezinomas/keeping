from django.apps import AppConfig
from django.db.models.signals import post_save

App_name = "expenses"


class ExpensesConfig(AppConfig):
    name = "project.expenses"

    def ready(self):
        from ..core.services.signals_service import BalanceKind, register_sources
        from ..core.signals import (
            accounts_signal,
            connect_save_and_delete,
            update_journal_first_record,
        )
        from .models import Expense
        from .services.model_services import ExpenseModelService

        connect_save_and_delete(accounts_signal, Expense)
        post_save.connect(update_journal_first_record, sender=Expense)

        register_sources(
            self.label,
            BalanceKind.ACCOUNTS,
            "expenses",
            lambda user: ExpenseModelService(user).expenses(),
        )
