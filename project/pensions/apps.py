from django.apps import AppConfig
from django.db.models.signals import post_save


class PensionsConfig(AppConfig):
    name = "project.pensions"

    def ready(self):
        from ..core.services.signals_service import (
            BalanceKind,
            register_balance,
            register_sources,
        )
        from ..core.signals import connect_save_and_delete, pensions_signal
        from .models import Pension, PensionType
        from .services.model_services import (
            PensionBalanceModelService,
            PensionModelService,
            PensionTypeModelService,
        )
        from .signals import pension_type_signal

        connect_save_and_delete(pensions_signal, Pension)
        post_save.connect(pension_type_signal, sender=PensionType)

        pensions = BalanceKind.PENSIONS
        register_sources(
            self.label,
            pensions,
            "incomes",
            lambda user: PensionModelService(user).incomes(),
        )
        register_sources(
            self.label,
            pensions,
            "types",
            lambda user: PensionTypeModelService(user).items(),
        )
        register_balance(pensions, PensionBalanceModelService)
