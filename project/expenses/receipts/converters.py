import re
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation

from .errors import UnreadableReceiptTextError
from .layout import Unit

_WHITESPACE = re.compile(r"\s+")
_MONEY = re.compile(r"^€(\d+,\d{2})$")
_AMOUNT = re.compile(r"^(\d+(?:,\d+)?) (\S+?)\.?$")


def cell(value: str | None) -> str:
    text = ""
    if value is not None:
        text = value
    return _WHITESPACE.sub(" ", text).strip()


def money(text: str) -> int:
    match = _MONEY.match(text)
    if match is None:
        raise UnreadableReceiptTextError(text)
    return int(Decimal(match.group(1).replace(",", ".")) * 100)


def amount(text: str, unit_words: Mapping[str, Unit]) -> int:
    match = _AMOUNT.match(text)
    if match is None:
        raise UnreadableReceiptTextError(text)

    number, word = match.group(1), match.group(2)
    unit = unit_words.get(word)
    if unit == Unit.WEIGHT:
        return 1
    if unit == Unit.PIECES and "," not in number:
        return int(number)

    raise UnreadableReceiptTextError(text)


def is_deposit(title: str, deposit_words: tuple[str, ...]) -> bool:
    return any(word in title for word in deposit_words)
