from dataclasses import dataclass
from typing import Dict, List


@dataclass()
class NoIncomes():
    money: float
    fund: float
    pension: float
    avg_expenses: float
    cut_sum: float

    @property
    def summary(self) -> List[Dict[str, float]]:
        i1 = self.money + self.fund
        i2 = i1 + self.pension
        cut_sum = 0 if not self.cut_sum else self.cut_sum

        return [{
            'label': 'money',
            'money_fund': i1,
            'money_fund_pension': i2
        }, {
            'label': 'no_cut',
            'money_fund': self._div(i1, self.avg_expenses),
            'money_fund_pension': self._div(i2, self.avg_expenses)
        }, {
            'label': 'cut',
            'money_fund': self._div(i1, (self.avg_expenses - cut_sum)),
            'money_fund_pension': self._div(i2, (self.avg_expenses - cut_sum))
        }]

    def _div(self, incomes: float, expenses: float) -> float:
        _val = 0.0

        if expenses:
            _val = incomes / expenses

        return _val
