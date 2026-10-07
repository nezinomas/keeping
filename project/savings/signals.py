from ..bookkeeping import balance_sources
from ..core.services.signals_service import journal_user
from .models import SavingType


# A type's fee source and close year change its balances.
def saving_type_signal(sender: object, instance: SavingType, *args, **kwargs):
    user = journal_user(instance)
    balance_sources.sync_accounts(user)
    balance_sources.sync_savings(user)
