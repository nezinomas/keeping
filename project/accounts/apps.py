from django.apps import AppConfig

App_name = "accounts"


class AccountsConfig(AppConfig):
    name = name = f"project.{App_name}"

    def ready(self):
        from ..core.services.signals_service import (
            BalanceKind,
            register_balance,
            register_sources,
        )
        from .services.model_services import (
            AccountBalanceModelService,
            AccountModelService,
        )

        register_sources(
            self.label,
            BalanceKind.ACCOUNTS,
            "types",
            lambda user: AccountModelService(user).all(),
        )
        register_balance(BalanceKind.ACCOUNTS, AccountBalanceModelService)
