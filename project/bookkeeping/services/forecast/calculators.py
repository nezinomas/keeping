import statistics

from .dtos import AveragesDTO, CurrentMonthDTO, ForecastDataDTO


class ForecastCalculator:
    def __init__(self, month: int, data: ForecastDataDTO):
        self._month = month
        self._data = data
        self._past_idx = self._month - 1

    def balance(self) -> float:
        incomes = sum(self._data.incomes[: self._past_idx])
        savings_close = sum(self._data.savings_close[: self._past_idx])
        expenses = sum(self._data.expenses[: self._past_idx])
        savings = sum(self._data.savings[: self._past_idx])

        return incomes + savings_close - expenses - savings

    def planned_incomes(self) -> float:
        return sum(self._data.planned_incomes[self._month :])

    def medians(self) -> AveragesDTO:
        past_expenses = self._data.expenses[: self._past_idx]
        past_savings = self._data.savings[: self._past_idx]

        return AveragesDTO(
            expenses=statistics.median(past_expenses) if past_expenses else 0.0,
            savings=statistics.median(past_savings) if past_savings else 0.0,
        )

    def current_month(self) -> CurrentMonthDTO:
        idx = self._past_idx
        return CurrentMonthDTO(
            expenses=float(self._data.expenses[idx]),
            savings=float(self._data.savings[idx]),
            incomes=float(self._data.incomes[idx]),
            planned_incomes=float(self._data.planned_incomes[idx]),
        )

    def forecast(self) -> float:
        avg = self.medians()
        current = self.current_month()
        months_left = 12 - self._month

        expenses = max(current.expenses, avg.expenses)
        savings = max(current.savings, avg.savings)
        incomes = max(current.incomes, current.planned_incomes)

        return (
            self.balance()
            + self.planned_incomes()
            + incomes
            - (expenses + avg.expenses * months_left)
            - (savings + avg.savings * months_left)
        )
