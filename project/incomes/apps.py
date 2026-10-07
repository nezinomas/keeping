from django.apps import AppConfig
from django.db.models.signals import post_save


class IncomesConfig(AppConfig):
    name = "project.incomes"

    def ready(self):
        from ..core.signals import (
            accounts_signal,
            connect_save_and_delete,
            update_journal_first_record,
        )
        from .models import Income

        connect_save_and_delete(accounts_signal, Income)
        post_save.connect(update_journal_first_record, sender=Income)
