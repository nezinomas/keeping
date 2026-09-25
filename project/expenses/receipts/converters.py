import re
from collections.abc import Mapping
from decimal import Decimal

from .errors import UnreadableReceiptTextError
from .layout import Unit

_WHITESPACE = re.compile(r"\s+")
# a minus only on the bare form: no sample has shown a negative euro price
_MONEY = re.compile(r"^(€|-?)(\d+,\d{2})$")
_AMOUNT = re.compile(r"^(\d+(?:,\d+)?) (\S+?)\.?$")


def _text(value: str | None) -> str:
    text = ""
    if value is not None:
        text = value
    return text


def cell(value: str | None) -> str:
    return _WHITESPACE.sub(" ", _text(value)).strip()


def lines(value: str | None) -> tuple[str, ...]:
    return tuple(cell(line) for line in _text(value).splitlines())


def is_money(text: str) -> bool:
    return _MONEY.match(text) is not None


def money(text: str) -> int:
    match = _MONEY.match(text)
    if match is None:
        raise UnreadableReceiptTextError(text)
    sign, digits = match.groups()
    cents = int(Decimal(digits.replace(",", ".")) * 100)
    if sign == "-":
        cents = -cents
    return cents


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
