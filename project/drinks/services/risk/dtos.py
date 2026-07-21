from dataclasses import dataclass, field


@dataclass(frozen=True)
class RiskDto:
    current_daily: list = field(default_factory=list)
    past_daily: list = field(default_factory=list)
