from dataclasses import dataclass


@dataclass(frozen=True)
class DailyLimit:
    amount: float
    is_set: bool = True

    def __post_init__(self):
        if self.amount <= 0:
            raise ValueError(f"a set Limit needs an amount above 0, not {self.amount}")


@dataclass(frozen=True)
class NoDailyLimit:
    """No Drink Target: the chart draws no limit line and no harm zone."""

    amount: float = 0.0
    is_set: bool = False
