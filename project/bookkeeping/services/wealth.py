from django.db.models import Sum

from ...accounts.models import AccountBalance
from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


class WealthService():
    def __init__(self, year: int):
        self.account_sum = self._get_account_sum(year)
        self.saving_sum = self._get_saving_sum(year)
        self.pension_sum = self._get_pension_sum(year)

    def _get_account_sum(self, year: int) -> float:
        return \
            AccountBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('balance')) \
            ['balance__sum'] or 0.0

    def _get_saving_sum(self, year: int) -> float:
        return \
            SavingBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('market_value')) \
            ['market_value__sum'] or 0.0

    def _get_pension_sum(self, year: int) -> float:
        return \
            PensionBalance.objects \
            .related() \
            .filter(year=year) \
            .aggregate(Sum('market_value')) \
            ['market_value__sum'] or 0.0

    @property
    def money(self):
        return \
            self.account_sum + self.saving_sum

    @property
    def wealth(self):
        return \
            self.account_sum + self.saving_sum + self.pension_sum
