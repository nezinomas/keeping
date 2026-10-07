from django.apps import AppConfig
from django.db.models.signals import post_save

App_name = "bookkeeping"


class BookkeepingConfig(AppConfig):
    name = f"project.{App_name}"

    def ready(self):
        from ..core.signals import accounts_signal, pensions_signal, savings_signal
        from .models import AccountWorth, PensionWorth, SavingWorth

        post_save.connect(accounts_signal, sender=AccountWorth)
        post_save.connect(savings_signal, sender=SavingWorth)
        post_save.connect(pensions_signal, sender=PensionWorth)
