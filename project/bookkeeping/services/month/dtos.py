from dataclasses import dataclass


@dataclass(frozen=True)
class MonthDataDTO:
    incomes: int
    expenses: list[dict]
    expense_types: list[str]
    necessary_expense_types: list[str]
    savings: list[dict]
    plans_data: dict
    targets: dict


@dataclass(frozen=True)
class InfoState:
    income: int
    saving: int
    expense: int
    per_day: int
    balance: int
