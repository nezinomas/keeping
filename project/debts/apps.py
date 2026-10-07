from django.apps import AppConfig

App_name = "debts"


class DebtsConfig(AppConfig):
    name = f"project.{App_name}"

    def ready(self):
        from ..core.signals import accounts_signal, connect_save_and_delete
        from .models import Debt, DebtReturn

        connect_save_and_delete(accounts_signal, Debt, DebtReturn)
        # after the connect: accounts_signal must run before update_debt_model
        from .signals import update_debt_model  # noqa: F401
