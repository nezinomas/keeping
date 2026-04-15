from dataclasses import dataclass


@dataclass(frozen=True)
class DetailedDto:
    data: list[dict]
