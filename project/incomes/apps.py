from django.apps import AppConfig


class IncomesConfig(AppConfig):
    name = "project.incomes"

    def ready(self):
        from ..core.signals import (  # noqa: F401
            accounts_signal,
            update_journal_first_record,
        )
