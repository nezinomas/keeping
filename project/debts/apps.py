from django.apps import AppConfig

App_name = "debts"


class DebtsConfig(AppConfig):
    name = f"project.{App_name}"

    def ready(self):
        from ..core.services.signals_service import BalanceKind, register_sources
        from ..core.signals import accounts_signal, connect_save_and_delete
        from .models import Debt, DebtReturn
        from .services.model_services import DebtModelService, DebtReturnModelService

        connect_save_and_delete(accounts_signal, Debt, DebtReturn)
        # after the connect: accounts_signal must run before update_debt_model
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
