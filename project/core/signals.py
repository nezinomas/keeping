from typing import Dict, List

from crequest.middleware import CrequestMiddleware
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..accounts.lib.balance import Balance as AccountStats
from ..accounts.models import Account, AccountBalance
from ..bookkeeping.lib.summary import collect_summary_data
from ..bookkeeping.models import AccountWorth, SavingWorth
from ..expenses.models import Expense, ExpenseType
from ..incomes.models import Income, IncomeType
from ..savings.lib.balance import Balance as SavingStats
from ..savings.models import Saving, SavingBalance, SavingType
from ..transactions.models import SavingChange, SavingClose, Transaction


# ----------------------------------------------------------------------------
#                                                               AccountBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=Income)
@receiver(post_save, sender=IncomeType)
@receiver(post_save, sender=Expense)
@receiver(post_save, sender=ExpenseType)
@receiver(post_save, sender=Saving)
@receiver(post_save, sender=SavingType)
@receiver(post_save, sender=Transaction)
@receiver(post_save, sender=SavingClose)
@receiver(post_save, sender=AccountWorth)
def post_save_account_stats(instance: object, year: int = None,
                            *args, **kwargs):
    SignalBase.post_save_accounts(instance, year)


# ----------------------------------------------------------------------------
#                                                               SavingBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=Saving)
@receiver(post_save, sender=SavingType)
@receiver(post_save, sender=SavingClose)
@receiver(post_save, sender=SavingChange)
@receiver(post_save, sender=SavingWorth)
def post_save_saving_stats(instance: object, year: int = None,
                           *args, **kwargs):
    SignalBase.post_save_savings(instance, year)


# ----------------------------------------------------------------------------
#                                                   post_save SignalBase class
# ----------------------------------------------------------------------------
class SignalBase():
    def __init__(self, instance: object, year: int = None):
        if not year:
            request = CrequestMiddleware.get_request()
            self.year = request.user.profile.year
        else:
            self.year = year

        self.instance = instance

        self._update_or_create()

    @classmethod
    def post_save_accounts(cls, instance: object, year: int):
        cls.field = 'account_id'
        cls.model_types = Account
        cls.model_balance = AccountBalance
        cls.model_worth = AccountWorth
        cls.class_stats = AccountStats
        cls.summary_models = 'accounts'

        return cls(instance, year)

    @classmethod
    def post_save_savings(cls, instance: object, year: int):
        cls.field = 'saving_type_id'
        cls.model_types = SavingType
        cls.model_balance = SavingBalance
        cls.model_worth = SavingWorth
        cls.class_stats = SavingStats
        cls.summary_models = 'savings'

        return cls(instance, year)

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
