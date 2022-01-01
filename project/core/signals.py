from typing import Dict, List

from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from ..accounts.lib.balance import Balance as AccountStats
from ..accounts.models import Account, AccountBalance
from ..bookkeeping.models import AccountWorth, PensionWorth, SavingWorth
from ..debts.models import Borrow, BorrowReturn, Lent, LentReturn
from ..expenses.models import Expense
from ..incomes.models import Income
from ..pensions.models import Pension, PensionBalance, PensionType
from ..savings.lib.balance import Balance as SavingStats
from ..savings.models import Saving, SavingBalance, SavingType
from ..transactions.models import SavingChange, SavingClose, Transaction
from .lib import utils
from .lib.summary import (AccountsBalanceModels, PensionsBalanceModels,
                          SavingsBalanceModels, collect_summary_data)


# ----------------------------------------------------------------------------
#                                                               AccountBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=Income)
@receiver(post_delete, sender=Income)
@receiver(post_save, sender=Expense)
@receiver(post_delete, sender=Expense)
@receiver(post_save, sender=Saving)
@receiver(post_delete, sender=Saving)
@receiver(post_save, sender=Transaction)
@receiver(post_delete, sender=Transaction)
@receiver(post_save, sender=SavingClose)
@receiver(post_delete, sender=SavingClose)
@receiver(post_save, sender=AccountWorth)
@receiver(post_save, sender=Borrow)
@receiver(post_delete, sender=Borrow)
@receiver(post_save, sender=BorrowReturn)
@receiver(post_delete, sender=BorrowReturn)
@receiver(post_save, sender=Lent)
@receiver(post_delete, sender=Lent)
@receiver(post_save, sender=LentReturn)
@receiver(post_delete, sender=LentReturn)
def accounts_post_signal(sender: object,
                         instance: object,
                         year: int = None,
                         types: Dict[str, int] = None,
                         *args, **kwargs):
    SignalBase.accounts(sender, instance, year, types)


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
def savings_post_signal(sender: object,
                        instance: object,
                        year: int = None,
                        types: Dict[str, int] = None,
                        *args, **kwargs):
    SignalBase.savings(sender, instance, year, types)


# ----------------------------------------------------------------------------
#                                                               PensionBalance
# ----------------------------------------------------------------------------
@receiver(post_save, sender=Pension)
@receiver(post_delete, sender=Pension)
@receiver(post_save, sender=PensionWorth)
def pensions_post_signal(sender: object,
                         instance: object,
                         year: int = None,
                         types: Dict[str, int] = None,
                        *args, **kwargs):
    SignalBase.pensions(sender, instance, year, types)


# ----------------------------------------------------------------------------
#                                                   post_save SignalBase class
# ----------------------------------------------------------------------------
class SignalBase():
    field = None

    def __init__(self,
                 instance: object,
                 year: int = None,
                 types: Dict[str, int] = None):

        if not year:
            self.year = utils.get_user().year
        else:
            self.year = year

        self.instance = instance
        self.types = types

        self._update_or_create()

    @classmethod
    def accounts(cls,
                 sender: object,
                 instance: object,
                 year: int = None,
                 types: Dict[str, int] = None):

        cls.field = 'account_id'
        cls.model_types = Account
        cls.model_balance = AccountBalance
        cls.model_worth = AccountWorth
        cls.class_stats = AccountStats
        cls.summary_models = AccountsBalanceModels
        cls.sender = sender

        return cls(instance, year, types)

    @classmethod
    def savings(cls,
                sender: object,
                instance: object,
                year: int = None,
                types: Dict[str, int] = None):

        cls.field = 'saving_type_id'
        cls.model_types = SavingType
        cls.model_balance = SavingBalance
        cls.model_worth = SavingWorth
        cls.class_stats = SavingStats
        cls.summary_models = SavingsBalanceModels
        cls.sender = sender

        return cls(instance, year, types)

    @classmethod
    def pensions(cls,
                 sender: object,
                 instance: object,
                 year: int = None,
                 types: Dict[str, int] = None):

        cls.field = 'pension_type_id'
        cls.model_types = PensionType
        cls.model_balance = PensionBalance
        cls.model_worth = PensionWorth
        cls.class_stats = SavingStats  # using same savings Balance class
        cls.summary_models = PensionsBalanceModels
        cls.sender = sender

        return cls(instance, year, types)

    def _update_or_create(self) -> None:
        stats = self._get_stats()

        for row in stats:
            # get id
            _id = row['id']

            # delete dictionary keys
            del row['id']
            del row['title']

            self.model_balance.objects.update_or_create(
                year=self.year,
                **{self.field: _id},
                defaults={k: v for k, v in row.items()}
            )

    def _get_worth(self) -> List[Dict]:
        return self.model_worth.objects.items(year=self.year)

    def _get_id(self) -> List[int]:
        account_id = []
        field_list = [self.field, 'from_account_id', 'to_account_id']

        for name in field_list:
            _id = getattr(self.instance, name, None)
            if _id:
                account_id.append(_id)

        # list of original, before change, account_id values
        if hasattr(self.instance, '_old_values'):
            account_id = list(set(account_id + self.instance._old_values))

        return account_id

    def _get_accounts(self) -> Dict[str, int]:
        # qs = self.model_types.objects.items(year=self.year)
        # items method automatically filters closed type
        # but in signals i need custom closed types filtering
        qs = self.model_types.objects.related()

        account_id = self._get_id()
        if account_id:
            qs = qs.filter(id__in=account_id)

        # filter closed [accounts, savings, pensions]
        if getattr(self.model_types, 'closed', False):
            while(True):
                if not self.field:
                    break

                # if [account] leave current year
                if self.field == 'account_id':
                    qs = qs.filter(
                        Q(closed__isnull=True) |
                        Q(closed__gte=self.year)
                    )
                else:  # if [savings, pensions] filter and current year
                    qs = qs.filter(
                        Q(closed__isnull=True) |
                        Q(closed__gt=self.year)
                    )

                break

        qs = qs.values('id', 'title')

        return {x['title']: x['id'] for x in qs}

    def _get_stats(self) -> List[Dict]:
        # get (account_types|savings_types|pension_types) in class if types is empty
        if not self.types:
            account = self._get_accounts()
        else:
            account = self.types

        worth = self._get_worth()

        data = collect_summary_data(
            year=self.year,
            types=account,
            where=self.summary_models
        )

        return self.class_stats(data, worth).balance
