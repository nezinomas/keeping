from django.apps import AppConfig


class SavingsConfig(AppConfig):
    name = "project.savings"

    def ready(self):
        from ..core.services.signals_service import (
            BalanceKind,
            register_balance,
            register_sources,
        )
        from ..core.signals import accounts_signal, savings_signal  # noqa: F401
        from .services.model_services import (
            SavingBalanceModelService,
            SavingModelService,
            SavingTypeModelService,
        )

        accounts, savings = BalanceKind.ACCOUNTS, BalanceKind.SAVINGS
        register_sources(
            self.label,
            accounts,
            "expenses",
            lambda user: SavingModelService(user).expenses(),
        )
        register_sources(
            self.label,
            savings,
            "incomes",
            lambda user: SavingModelService(user).incomes(),
        )
        register_sources(
            self.label,
            savings,
            "types",
            lambda user: SavingTypeModelService(user).all(),
        )
        register_balance(savings, SavingBalanceModelService)
