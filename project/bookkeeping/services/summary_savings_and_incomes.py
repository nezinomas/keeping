from dataclasses import dataclass, field
from datetime import date

from django.utils.translation import gettext as _

from ...core.lib.date import years_to_date
from ...incomes.services.model_services import IncomeModelService
from ...savings.services.model_services import SavingModelService
from ...users.models import User


@dataclass
class Data:
    user: User
    incomes: list = field(init=False, default_factory=list)
    savings: list = field(init=False, default_factory=list)

    def __post_init__(self):
        self.incomes = IncomeModelService(self.user).sum_by_year()
        self.savings = SavingModelService(self.user).sum_by_year()


class Service:
    def __init__(self, data: Data, years: list[int]):
        self._years = years
        self._incomes = data.incomes
        self._savings = data.savings

    def chart_data(self):
        incomes_by_year = {x["year"]: x["sum"] for x in self._incomes}
        savings_by_year = {x["year"]: x["sum"] for x in self._savings}

        incomes, savings, percents = [], [], []
        for year in self._years:
            income = incomes_by_year.get(year, 0)
            saving = savings_by_year.get(year, 0)
            percent = (saving * 100) / income if income else 0

            incomes.append(income)
            savings.append(saving)
            percents.append(percent)

        return {
            "categories": self._years,
            "incomes": incomes,
            "savings": savings,
            "percents": percents,
        }


def load_service(user: User, today: date) -> dict:
    data = Data(user)
    obj = Service(data, years_to_date(user, today))

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
