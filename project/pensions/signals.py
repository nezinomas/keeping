from ..bookkeeping import balance_sources
from ..core.services.signals_service import journal_user
from .models import PensionType


# Closing a type drops its later rows, so the sync runs on the type itself.
def pension_type_signal(sender: object, instance: PensionType, *args, **kwargs):
    balance_sources.sync_pensions(journal_user(instance))
