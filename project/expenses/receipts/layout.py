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
    promotion_label: str
    unit_words: Mapping[str, Unit] = DEFAULT_UNIT_WORDS
    deposit_words: tuple[str, ...] = DEFAULT_DEPOSIT_WORDS


@dataclass(frozen=True)
class TextLayout:
    marker: str
    lines_start: str
    lines_end: str
    vat_classes: tuple[str, ...]
    amount_separator: str
    item_discount_prefixes: tuple[str, ...]
    shop_money_label: str
    total_label: str
    unit_words: Mapping[str, Unit] = DEFAULT_UNIT_WORDS
    deposit_words: tuple[str, ...] = DEFAULT_DEPOSIT_WORDS
