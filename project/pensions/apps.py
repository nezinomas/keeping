from django.apps import AppConfig


class PensionsConfig(AppConfig):
    name = "project.pensions"

    def ready(self):
        from ..core.services.signals_service import (
            BalanceKind,
            register_balance,
            register_sources,
        )
        from ..core.signals import pensions_signal  # noqa: F401
        from .services.model_services import (
            PensionBalanceModelService,
            PensionModelService,
            PensionTypeModelService,
        )

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
