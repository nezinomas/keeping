from django.apps import AppConfig

App_name = "debts"


class DebtsConfig(AppConfig):
    name = f"project.{App_name}"

    def ready(self):
        # bookkeeping's ready() ran first: accounts_signal precedes update_debt_model
        from .signals import update_debt_model  # noqa: F401
