from ..core.services import signals_service
from .models import PensionType


# Closing a type drops its later rows, so the sync runs on the type itself.
def pension_type_signal(sender: object, instance: PensionType, *args, **kwargs):
    signals_service.sync_pensions(signals_service.journal_user(instance))
