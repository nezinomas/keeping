
from dataclasses import dataclass


@dataclass(frozen=True)
class IndexDataDTO:
    amount_start: int
    monthly_data: list[dict]
    debts: dict[str, dict]