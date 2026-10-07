from django.apps import AppConfig

App_name = "bookkeeping"


class BookkeepingConfig(AppConfig):
    name = f"project.{App_name}"

    def ready(self):
        from ..core.services.signals_service import BalanceKind, register_sources
        from .services.model_services import (
            AccountWorthModelService,
            PensionWorthModelService,
            SavingWorthModelService,
        )

        register_sources(
            self.label,
            BalanceKind.ACCOUNTS,
            "have",
            lambda user: AccountWorthModelService(user).have(),
        )
        register_sources(
            self.label,
            BalanceKind.SAVINGS,
            "have",
            lambda user: SavingWorthModelService(user).have(),
        )
        register_sources(
            self.label,
            BalanceKind.PENSIONS,
            "have",
            lambda user: PensionWorthModelService(user).have(),
        )
