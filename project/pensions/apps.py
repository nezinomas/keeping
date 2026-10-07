from django.apps import AppConfig
from django.db.models.signals import post_save


class PensionsConfig(AppConfig):
    name = "project.pensions"

    def ready(self):
        from ..core.signals import connect_save_and_delete, pensions_signal
        from .models import Pension, PensionType
        from .signals import pension_type_signal

        connect_save_and_delete(pensions_signal, Pension)
        post_save.connect(pension_type_signal, sender=PensionType)
