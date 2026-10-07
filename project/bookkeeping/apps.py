from django.apps import AppConfig
from django.db.models.signals import post_save

App_name = "bookkeeping"


class BookkeepingConfig(AppConfig):
    name = f"project.{App_name}"

    def ready(self):
        from ..core.services.signals_service import BalanceKind, register_sources
        from ..core.signals import accounts_signal, pensions_signal, savings_signal
        from .models import AccountWorth, PensionWorth, SavingWorth
        from .services.model_services import (
            AccountWorthModelService,
            PensionWorthModelService,
            SavingWorthModelService,
        )

        post_save.connect(accounts_signal, sender=AccountWorth)
        post_save.connect(savings_signal, sender=SavingWorth)
        post_save.connect(pensions_signal, sender=PensionWorth)

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
