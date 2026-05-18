from dataclasses import dataclass, field

@dataclass(frozen=True)
class IndexDataDTO:
    year: int
    amount_start: int
    monthly_data: list[dict]
    debts: dict[str, dict]
    savings_goal: float = 0.0
    top_categories: list[dict] = field(default_factory=list)
