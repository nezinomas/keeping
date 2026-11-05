from dataclasses import dataclass


@dataclass(frozen=True)
class FilterItem:
    label: str
    url: str
    active: bool
