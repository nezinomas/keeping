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
        save_sum = 0 if not self.save_sum else self.save_sum

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
            'money_fund': self._div(i1, (self.avg_expenses - save_sum)),
            'money_fund_pension': self._div(i2, (self.avg_expenses - save_sum))
        }]

    @property
    def save_sum(self) -> float:
        _ret = None

        if self.not_use and self.avg_expenses:
            _ret = sum(self.avg_type_expenses.get(name, 0.0) for name in self.not_use)

        if _ret == 0:
            _ret = None

        return _ret

    def _div(self, incomes: float, expenses: float) -> float:
        _val = 0.0

        if expenses:
            _val = incomes / expenses

        return _val
