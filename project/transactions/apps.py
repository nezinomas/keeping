from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    name = "project.transactions"

    def ready(self):
        from ..core.services.signals_service import BalanceKind, register_sources
        from ..core.signals import accounts_signal, connect_save_and_delete
        from .models import SavingChange, SavingClose, Transaction
        from .services.model_services import (
            SavingChangeModelService,
            SavingCloseModelService,
            TransactionModelService,
        )
        from .signals import move_signal

        connect_save_and_delete(accounts_signal, Transaction, SavingClose)
        connect_save_and_delete(move_signal, SavingClose, SavingChange)

        accounts, savings = BalanceKind.ACCOUNTS, BalanceKind.SAVINGS
        register_sources(
            self.label,
            accounts,
            "incomes",
            lambda user: TransactionModelService(user).incomes(),
            lambda user: SavingCloseModelService(user).incomes(),
        )
        register_sources(
            self.label,
            accounts,
            "expenses",
            lambda user: TransactionModelService(user).expenses(),
        )
        register_sources(
            self.label,
            savings,
            "incomes",
            lambda user: SavingChangeModelService(user).incomes(),
        )
        register_sources(
            self.label,
            savings,
            "expenses",
            lambda user: SavingCloseModelService(user).expenses(),
            lambda user: SavingChangeModelService(user).expenses(),
        )
        register_sources(
            self.label,
            savings,
            "moves",
            lambda user: SavingCloseModelService(user).moves(),
            lambda user: SavingChangeModelService(user).moves(),
        )
