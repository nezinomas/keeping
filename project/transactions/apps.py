from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    name = "project.transactions"

    def ready(self):
        from ..core.signals import accounts_signal, connect_save_and_delete
        from .models import SavingChange, SavingClose, Transaction
        from .signals import move_signal

        connect_save_and_delete(accounts_signal, Transaction, SavingClose)
        connect_save_and_delete(move_signal, SavingClose, SavingChange)
