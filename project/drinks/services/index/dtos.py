from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class IndexDto:
    sum_by_month: list
    sum_by_day: list
    target: float = 0.0
    latest_past_date: date | None = None
    latest_current_date: date | None = None
