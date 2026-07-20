from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrendsDto:
    current_daily: list = field(default_factory=list)
    past_daily: list = field(default_factory=list)
    target: float = 0.0
