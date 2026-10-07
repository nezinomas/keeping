from django.apps import AppConfig

App_name = "expenses"


class ExpensesConfig(AppConfig):
    name = "project.expenses"

    def ready(self):
        from ..core.services.signals_service import BalanceKind, register_sources
        from ..core.signals import (  # noqa: F401
            accounts_signal,
            update_journal_first_record,
        )
        from .services.model_services import ExpenseModelService

        register_sources(
            self.label,
            BalanceKind.ACCOUNTS,
            "expenses",
            lambda user: ExpenseModelService(user).expenses(),
        )
