from dataclasses import dataclass, field
from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving
from ...plans.models import IncomePlan
from ...core.lib.date import monthnames


@dataclass
class ForecastServiceData:
    year: int
    data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.data = {
            "incomes": self.get_data(Income),
            "expenses": self.get_data(Expense),
            "savings": self.get_data(Saving),
            "planned_incomes": self.get_planned_incomes(),
        }

    def get_data(self, model):
        return [x["sum"] for x in model.objects.sum_by_month(self.year)]

    def get_planned_incomes(self):
        data = IncomePlan.objects.year(self.year).values(*monthnames())
        return list(data[0].values()) if data else []
