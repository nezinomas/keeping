from ..core.services import signals_service
from .models import SavingType


# A type's fee source and close year change its balances.
def saving_type_signal(sender: object, instance: SavingType, *args, **kwargs):
    user = signals_service.journal_user(instance)
    signals_service.sync_accounts(user)
    signals_service.sync_savings(user)
