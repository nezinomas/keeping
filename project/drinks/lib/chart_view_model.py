from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ChartViewModel:
    """Fieldless, so a subclass is free to declare fields without defaults."""

    @property
    def as_dict(self) -> dict:
        return asdict(self)
