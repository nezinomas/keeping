from dataclasses import dataclass, field

from ...core.lib.date import years
from ...incomes.models import Income
from ...savings.models import Saving


@dataclass
class ServiceSummarySavingsAndIncomesData:
    incomes: list = field(init=False, default_factory=list)
    savings: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = Income.objects.sum_by_year()
        self.savings = Saving.objects.sum_by_year()


class ServiceSummarySavingsAndIncomes:
    def __init__(self, data: ServiceSummarySavingsAndIncomesData):
        self._incomes = data.incomes
        self._savings = data.savings

    def chart_data(self):
        _categories = years()[:-1]
        _incomes = {x["year"]: x["sum"] for x in self._incomes}
        _savings = {x["year"]: x["sum"] for x in self._savings}

        return {
            "categories": _categories,
            "incomes": [_incomes.get(year, 0) for year in _categories],
            "savings": [_savings.get(year, 0) for year in _categories],
        }
