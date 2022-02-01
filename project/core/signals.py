from typing import Dict, List

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..bookkeeping.models import PensionWorth, SavingWorth
from ..pensions.models import Pension, PensionType
from ..savings.models import Saving, SavingType
from ..transactions.models import SavingChange, SavingClose
from .signals_base import SignalBase


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=Saving)
@receiver(post_delete, sender=Saving)
@receiver(post_save, sender=SavingClose)
@receiver(post_delete, sender=SavingClose)
@receiver(post_save, sender=SavingChange)
@receiver(post_delete, sender=SavingChange)
@receiver(post_save, sender=SavingWorth)
@receiver(post_save, sender=SavingType)
def savings_post_signal(sender: object,
                        instance: object,
                        year: int = None,
                        types: Dict[str, int] = None,
                        all_id: List[int] = None,
                        *args,
                        **kwargs):
    SignalBase.savings(sender, instance, year, types, all_id)


# ----------------------------------------------------------------------------
#                                                               PensionBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=Pension)
@receiver(post_delete, sender=Pension)
@receiver(post_save, sender=PensionWorth)
@receiver(post_save, sender=PensionType)
def pensions_post_signal(sender: object,
                         instance: object,
                         year: int = None,
                         types: Dict[str, int] = None,
                         all_id: List[int] = None,
                         *args,
                         **kwargs):
    SignalBase.pensions(sender, instance, year, types, all_id)
