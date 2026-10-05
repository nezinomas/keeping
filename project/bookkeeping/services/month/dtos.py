from dataclasses import dataclass, field


@dataclass(frozen=True)
class MonthDataDTO:
    incomes: int
    expenses: list[dict]
    expense_types: list[str]
    necessary_expense_types: list[str]
    savings: list[dict]
    plans_data: dict
    targets: dict
    account_fees: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class InfoState:
    income: int
    saving: int
    expense: int
    per_day: int
    balance: int
