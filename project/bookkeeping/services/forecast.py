from dataclasses import dataclass
from ...expenses.models import Expense
from ...incomes.models import Income
from ...savings.models import Saving
from ...plans.models import IncomePlan
from ...core.lib.date import monthnames


@dataclass
class ForecastServiceData:
    year: int

    def data(self):
        return {
            "incomes": self.get_data(Income.objects.sum_by_month(self.year)),
            "expenses": self.get_data(Expense.objects.sum_by_month(self.year)),
            "savings": self.get_data(Saving.objects.sum_by_month(self.year)),
            "planned_incomes": self.get_planned_data(
                IncomePlan.objects.year(self.year).values(*monthnames())
            ),
        }

    def get_data(self, data):
        arr = [0] * 12

        for row in data:
            month = row["date"].month
            arr[month - 1] = row["sum"]

        return arr

    def get_planned_data(self, data):
        arr = [0] * 12
        month_map = {month: i + 1 for i, month in enumerate(monthnames())}

        for row in data:
            for k, v in row.items():
                if not v:
                    continue

                month = month_map[k]
                arr[month - 1] += v
        return arr


class ForecastService:
    pass
