from django.apps import AppConfig


class IncomesConfig(AppConfig):
    name = "project.incomes"

    def ready(self):
        from ..core.services.signals_service import BalanceKind, register_sources
        from ..core.signals import (  # noqa: F401
            accounts_signal,
            update_journal_first_record,
        )
        from .services.model_services import IncomeModelService

        register_sources(
            self.label,
            BalanceKind.ACCOUNTS,
            "incomes",
            lambda user: IncomeModelService(user).incomes(),
        )
