from django.apps import AppConfig
from django.db.models.signals import post_save


class SavingsConfig(AppConfig):
    name = "project.savings"

    def ready(self):
        from ..core.signals import (
            accounts_signal,
            connect_save_and_delete,
            savings_signal,
        )
        from .models import Saving, SavingType
        from .signals import saving_type_signal

        connect_save_and_delete(accounts_signal, Saving)
        connect_save_and_delete(savings_signal, Saving)
        post_save.connect(saving_type_signal, sender=SavingType)
