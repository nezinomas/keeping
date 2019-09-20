from dataclasses import dataclass, field
from typing import Dict, List


@dataclass()
class NoIncomes():
    money: float
    fund: float
    pension: float
    avg_expenses: float
    avg_type_expenses: Dict[str, float] = field(default_factory=dict)
    not_use: List[str] = field(default_factory=list)

    @property
    def summary(self) -> List[Dict[str, float]]:
        i1 = self.money + self.fund
        i2 = i1 + self.pension
        not_use = self._not_use_sum(self.not_use, self.avg_type_expenses)

        return [{
            'not_use': 0,
            'money_fund': i1,
            'money_fund_pension': i2
        }, {
            'not_use': 0,
            'money_fund': self._div(i1, self.avg_expenses),
            'money_fund_pension': self._div(i2, self.avg_expenses)
        }, {
            'not_use': not_use,
            'money_fund': self._div(i1, (self.avg_expenses - not_use)),
            'money_fund_pension': self._div(i2, (self.avg_expenses - not_use))
        }]

    def _not_use_sum(self,
                     lst: List[str],
                     avg_type_expenses: Dict[str, float]) -> float:
        _sum = 0.0

        if lst:
            _sum = sum(avg_type_expenses.get(name, 0.0) for name in lst)

        return _sum

    def _div(self, incomes: float, expenses: float) -> float:
        _val = 0.0

        if expenses:
            _val = incomes / expenses

        return _val
