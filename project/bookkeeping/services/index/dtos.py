from dataclasses import dataclass

from ....debts.models import Debt


@dataclass(frozen=True)
class IndexDataDTO:
    amount_start: int
    monthly_data: list[dict]
    debts: dict[Debt.DebtType, dict]
