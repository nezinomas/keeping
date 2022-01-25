from typing import Dict, List

from django.db.models import Q

from ..accounts.lib.balance import Balance as AccountStats
from ..accounts.models import Account, AccountBalance
from ..bookkeeping.models import AccountWorth, PensionWorth, SavingWorth
from ..pensions.models import Pension, PensionBalance, PensionType
from ..savings.lib.balance import Balance as SavingStats
from ..savings.models import SavingBalance, SavingType
from ..transactions.models_hooks import transaction_accouts_hooks
from .lib import utils
from .lib.summary import (AccountsBalanceModels, PensionsBalanceModels,
                          SavingsBalanceModels, collect_summary_data)


class SignalBase():
    all_id = None
    field = None

    def __init__(self,
                 instance: object,
                 year: int = None,
                 types: Dict[str, int] = None,
                 all_id: List[int] = None):

        if not year:
            self.year = utils.get_user().year
        else:
            self.year = year

        self.instance = instance
        self.types = types
        self.all_id = self._get_id() if not all_id else all_id

        self._update_or_create()

    @classmethod
    def accounts(cls,
                 sender: object,
                 instance: object,
                 year: int = None,
                 types: Dict[str, int] = None,
                 all_id: List[int] = None):

        cls.field = 'account_id'
        cls.model_types = Account
        cls.model_balance = AccountBalance
        cls.model_worth = AccountWorth
        cls.class_stats = AccountStats
        cls.summary_models = AccountsBalanceModels
        cls.sender = sender

        return cls(instance, year, types, all_id)

    @classmethod
    def savings(cls,
                sender: object,
                instance: object,
                year: int = None,
                types: Dict[str, int] = None,
                all_id: List[int] = None):

        cls.field = 'saving_type_id'
        cls.model_types = SavingType
        cls.model_balance = SavingBalance
        cls.model_worth = SavingWorth
        cls.class_stats = SavingStats
        cls.summary_models = SavingsBalanceModels
        cls.sender = sender

        return cls(instance, year, types, all_id)

    @classmethod
    def pensions(cls,
                 sender: object,
                 instance: object,
                 year: int = None,
                 types: Dict[str, int] = None,
                 all_id: List[int] = None):

        cls.field = 'pension_type_id'
        cls.model_types = PensionType
        cls.model_balance = PensionBalance
        cls.model_worth = PensionWorth
        cls.class_stats = SavingStats  # using same savings Balance class
        cls.summary_models = PensionsBalanceModels
        cls.sender = sender

        return cls(instance, year, types, all_id)

    def _update_or_create(self) -> None:
        # copy by value all_id list
        arr = list(self.all_id)

        stats = self._get_stats()
        if stats:
            for row in stats:
                # get id
                _id = row['id']

                # remove from arr _id
                if _id in arr:
                    arr.remove(_id)

                # delete dictionary keys
                del row['id']
                del row['title']

                self.model_balance.objects.update_or_create(
                    year=self.year,
                    **{self.field: _id},
                    defaults={k: v for k, v in row.items()}
                )

        if arr:
            # if not empty arr, delete from balances rows
            q = (
                self.model_balance
                .objects
                .related()
                .filter(**{'year': self.year, f'{self.field}__in': arr})
                .delete()
            )

    def _get_field_list(self) -> List:
        field_list = [self.field]

        try:
            field_list += (
                transaction_accouts_hooks()
                .get(self.sender.__name__, {})
                .get(self.field, [])
            )
        except (TypeError, AttributeError):
            pass

        return field_list

    def _get_id(self) -> List[int]:
        account_id = []

        # if no instance return empty list
        if not self.instance:
            return account_id

        field_list = self._get_field_list()

        for name in field_list:
            _id = getattr(self.instance, name, None)
            if _id:
                account_id.append(_id)

        if not account_id:
            try:
                account_id.append(self.instance.pk)
            except AttributeError:
                pass

        # list of original, before change, account_id values
        if hasattr(self.instance, '_old_values'):
            _old_values = self.instance._old_values.get(self.field, [])
            account_id = list(set(account_id + _old_values))

        return account_id

    def _get_accounts(self) -> Dict[str, int]:
        if self.field == 'saving_type_id':
            qs = (
                self.model_types
                .objects
                .related()
                .filter(
                    Q(closed__isnull=True) | Q(closed__gt=self.year))
            )
        else:
            qs = (
                self.model_types
                .objects
                .items(year=self.year)
            )

        # filter created type from future
        qs = qs.filter(created__year__lte=self.year)

        # filter types only then exist sender and isntance
        if self.sender and self.instance:
            if self.all_id:
                qs = qs.filter(id__in=self.all_id)

        qs = qs.values('id', 'title')

        return {x['title']: x['id'] for x in qs}

    def _get_worth(self) -> List[Dict]:
        return self.model_worth.objects.items(year=self.year)

    def _get_stats(self) -> List[Dict]:
        # get (account_types|savings_types|pension_types) in class if types is empty
        if not self.types:
            account = self._get_accounts()
        else:
            account = self.types

        if not account:
            return None

        worth = self._get_worth()

        data = collect_summary_data(
            year=self.year,
            types=account,
            where=self.summary_models
        )

        return self.class_stats(data, worth).balance
