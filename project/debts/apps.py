from django.apps import AppConfig

App_name = "debts"


class DebtsConfig(AppConfig):
    name = f"project.{App_name}"

    def ready(self):
        from ..core.services.signals_service import BalanceKind, register_sources
        from ..core.signals import accounts_signal  # noqa: F401
        from .models import Debt
        from .services.model_services import DebtModelService, DebtReturnModelService
        from .signals import update_debt_model  # noqa: F401

        borrow, lend = Debt.DebtType.BORROW, Debt.DebtType.LEND
        accounts = BalanceKind.ACCOUNTS
        register_sources(
            self.label,
            accounts,
            "incomes",
            lambda user: DebtModelService(user, borrow).incomes(),
            lambda user: DebtReturnModelService(user, lend).incomes(),
        )
        register_sources(
            self.label,
            accounts,
            "expenses",
            lambda user: DebtModelService(user, lend).expenses(),
            lambda user: DebtReturnModelService(user, borrow).expenses(),
        )
