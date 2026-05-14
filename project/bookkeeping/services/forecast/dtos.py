from dataclasses import dataclass


@dataclass(frozen=True)
class ForecastDataDTO:
    incomes: list[int]
    expenses: list[int]
    savings: list[int]
    savings_close: list[int]
    planned_incomes: list[int]


@dataclass(frozen=True)
class AveragesDTO:
    expenses: float
    savings: float


@dataclass(frozen=True)
class CurrentMonthDTO:
    expenses: float
    savings: float
    incomes: float
    planned_incomes: float
