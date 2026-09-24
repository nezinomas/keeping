import types
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class Unit(StrEnum):
    PIECES = "pieces"
    WEIGHT = "weight"


DEFAULT_UNIT_WORDS = types.MappingProxyType({"vnt": Unit.PIECES, "kg": Unit.WEIGHT})
DEFAULT_DEPOSIT_WORDS = ("UŽSTATAS",)


@dataclass(frozen=True)
class Columns:
    title: str
    amount: str
    price: str

    @property
    def names(self) -> tuple[str, str, str]:
        return (self.title, self.amount, self.price)


@dataclass(frozen=True)
class TableLayout:
    marker: str
    columns: Columns
    total_label: str
    unit_words: Mapping[str, Unit] = DEFAULT_UNIT_WORDS
    deposit_words: tuple[str, ...] = DEFAULT_DEPOSIT_WORDS
