from typing import Dict, List

from crequest.middleware import CrequestMiddleware
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..accounts.lib.balance import Balance as AccountStats
from ..accounts.models import Account, AccountBalance
from ..bookkeeping.lib.summary import collect_summary_data
from ..bookkeeping.models import AccountWorth, SavingWorth
from ..expenses.models import Expense
from ..incomes.models import Income
from ..savings.lib.balance import Balance as SavingStats
from ..savings.models import Saving, SavingBalance, SavingType
from ..transactions.models import SavingChange, SavingClose, Transaction


# ----------------------------------------------------------------------------
#                                                               AccountBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=Income)
@receiver(post_save, sender=Expense)
@receiver(post_save, sender=Saving)
@receiver(post_save, sender=Transaction)
@receiver(post_save, sender=SavingClose)
@receiver(post_save, sender=AccountWorth)
def post_save_account_stats(instance, year=None, *args, **kwargs):
    class Cls(SignalBase):
        field = 'account_id'
        model_types = Account
        model_balance = AccountBalance
        model_worth = AccountWorth
        class_stats = AccountStats
        summary_models = 'accounts'

    Cls(instance=instance, year=year)


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=Saving)
@receiver(post_save, sender=SavingClose)
@receiver(post_save, sender=SavingChange)
@receiver(post_save, sender=SavingWorth)
def post_save_saving_stats(instance, year=None, *args, **kwargs):
    class Cls(SignalBase):
        field = 'saving_type_id'
        model_types = SavingType
        model_balance = SavingBalance
        model_worth = SavingWorth
        class_stats = SavingStats
        summary_models = 'savings'

    Cls(instance=instance, year=year)


# ----------------------------------------------------------------------------
#                                                   post_save SignalBase class
# ----------------------------------------------------------------------------
class SignalBase():
    def __init__(self, instance, year: int = None):
        if not year:
            request = CrequestMiddleware.get_request()
            self.year = request.user.profile.year
        else:
            self.year = year

        self.instance = instance

        self._update_or_create()

    def _update_or_create(self) -> None:
        stats = self._get_stats()

        for row in stats:
            # get id
            id = row['id']

            # delete dictionary keys
            del row['id']
            del row['title']

            obj, created = self.model_balance.objects.update_or_create(
                year=self.year,
                **{self.field: id},
                defaults={k: v for k, v in row.items()}
            )

    def _get_worth(self) -> List[Dict]:
        return self.model_worth.objects.items()

    def _get_id(self) -> List[int]:
        account_id = []
        field_list = [self.field, 'from_account_id', 'to_account_id']

        for name in field_list:
            id = getattr(self.instance, name, None)
            if id:
                account_id.append(id)

        return account_id

    def _get_accounts(self) -> Dict[str, int]:
        qs = self.model_types.objects.items(year=self.year)

        account_id = self._get_id()
        if account_id:
            qs = qs.filter(id__in=account_id)

        qs = qs.values('id', 'title')

        return {x['title']: x['id'] for x in qs}

    def _get_stats(self) -> List[Dict]:
        account = self._get_accounts()
        worth = self._get_worth()

        data = collect_summary_data(
            year=self.year,
            types=account,
            where=self.summary_models
        )

        return self.class_stats(data, worth).balance
