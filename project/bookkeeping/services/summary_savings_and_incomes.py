from dataclasses import dataclass, field

from django.utils.translation import gettext as _

from ...core.lib.date import years
from ...incomes.models import Income
from ...savings.models import Saving


@dataclass
class Data:
    incomes: list = field(init=False, default_factory=list)
    savings: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = Income.objects.sum_by_year()
        self.savings = Saving.objects.sum_by_year()


class Service:
    def __init__(self, data: Data):
        self._incomes = data.incomes
        self._savings = data.savings

    def chart_data(self):
        _categories = years()[:-1]
        _incomes = {x["year"]: x["sum"] for x in self._incomes}
        _savings = {x["year"]: x["sum"] for x in self._savings}

        _income_values, _saving_values, _percent_values = [], [], []
        for year in _categories:
            _income = _incomes.get(year, 0)
            _saving = _savings.get(year, 0)
            _percent = (_saving * 100) / _income if _income else 0

            _income_values.append(_income)
            _saving_values.append(_saving)
            _percent_values.append(_percent)

        return {
            "categories": _categories,
            "incomes": _income_values,
            "savings": _saving_values,
            "percents": _percent_values,
        }


def load_service() -> dict:
    data = Data()
    obj = Service(data)

    text = {
        "text": {
            "title": _("Incomes and Savings"),
            "incomes": _("Incomes"),
            "savings": _("Savings"),
            "percents": _("Percents"),
        }
    }

    return {
        "chart_data": obj.chart_data() | text,
    }
