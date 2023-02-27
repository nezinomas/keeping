from dataclasses import dataclass, field

from django.db.models import Sum

from ...accounts.models import AccountBalance
from ...pensions.models import PensionBalance
from ...savings.models import SavingBalance


@dataclass
class WealthServiceData:
    year: int

    account_balance: float = field(init=False, default=0)
    saving_balance: float = field(init=False, default=0)
    pension_balance: float = field(init=False, default=0)

    def __post_init__(self):
        self.account_balance = \
            AccountBalance.objects \
            .related() \
            .filter(year=self.year) \
            .aggregate(Sum('balance'))['balance__sum'] or 0

        self.saving_balance = \
            SavingBalance.objects \
            .related() \
            .filter(year=self.year) \
            .aggregate(Sum('market_value'))['market_value__sum'] or 0

        self.pension_balance = \
            PensionBalance.objects \
            .related() \
            .filter(year=self.year) \
            .aggregate(Sum('market_value'))['market_value__sum'] or 0


@dataclass
class WealthService:
    data: WealthServiceData

    @property
    def money(self):
        return 0 \
            + self.data.account_balance \
            + self.data.saving_balance

    @property
    def wealth(self):
        return 0 \
            + self.data.account_balance \
            + self.data.saving_balance \
            + self.data.pension_balance
