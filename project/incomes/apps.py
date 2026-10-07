from django.apps import AppConfig
from django.db.models.signals import post_save


class IncomesConfig(AppConfig):
    name = "project.incomes"

    def ready(self):
        from ..core.services.signals_service import BalanceKind, register_sources
        from ..core.signals import (
            accounts_signal,
            connect_save_and_delete,
            update_journal_first_record,
        )
        from .models import Income
        from .services.model_services import IncomeModelService

        connect_save_and_delete(accounts_signal, Income)
        post_save.connect(update_journal_first_record, sender=Income)

        register_sources(
            self.label,
            BalanceKind.ACCOUNTS,
            "incomes",
            lambda user: IncomeModelService(user).incomes(),
        )
