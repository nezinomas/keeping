from django.apps import AppConfig
from django.db.models.signals import post_save


class SavingsConfig(AppConfig):
    name = "project.savings"

    def ready(self):
        from ..core.services.signals_service import (
            BalanceKind,
            register_balance,
            register_sources,
        )
        from ..core.signals import (
            accounts_signal,
            connect_save_and_delete,
            savings_signal,
        )
        from .models import Saving, SavingType
        from .services.model_services import (
            SavingBalanceModelService,
            SavingModelService,
            SavingTypeModelService,
        )
        from .signals import saving_type_signal

        connect_save_and_delete(accounts_signal, Saving)
        connect_save_and_delete(savings_signal, Saving)
        post_save.connect(saving_type_signal, sender=SavingType)

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
