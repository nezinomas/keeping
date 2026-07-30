from dataclasses import dataclass

from ...core.lib.date import ydays

MAX_BOTTLES = 20

CANONICAL_TYPE = "stdav"


@dataclass(frozen=True)
class _DrinkRatio:
    stdav: float
    ml: float


_DRINK_RATIOS: dict[str, _DrinkRatio] = {
    "beer": _DrinkRatio(stdav=2.5, ml=500),  # 500ml  -> 2.5 std_av
    "wine": _DrinkRatio(stdav=8, ml=750),  # 750ml  -> 8   std_av
    "vodka": _DrinkRatio(stdav=40, ml=1000),  # 1000ml -> 40  std_av
    "stdav": _DrinkRatio(stdav=1, ml=10),  # 10ml   -> 1   std_av
}

_DEFAULT_RATIO = _DRINK_RATIOS["stdav"]


class DrinkConverter:
    def __init__(self, drink_type: str):
        self.drink_type = drink_type
        self._ratio = _DRINK_RATIOS.get(drink_type, _DEFAULT_RATIO)

    @property
    def ratio(self) -> float:
        return 1 / self._ratio.stdav

    @property
    def stdav_per_unit(self) -> float:
        return self._ratio.stdav

    def convert_qty(self, qty: float, to_type: str) -> float:
        target = _DRINK_RATIOS.get(to_type, _DEFAULT_RATIO)
        return (qty * self._ratio.stdav) / target.stdav

    def ml_to_stdav(self, ml: int | float) -> float:
        return (ml * self._ratio.stdav) / self._ratio.ml

    def stdav_to_ml(self, stdav: float) -> float:
        return (stdav * self._ratio.ml) / self._ratio.stdav

    @property
    def display_unit(self) -> str:
        """The unit an amount of this drink type is read in."""
        return "Std Av" if self.drink_type == CANONICAL_TYPE else "ml"

    @property
    def display_decimals(self) -> int:
        """A whole ml is precise enough; Std Av needs a decimal to survive."""
        return 1 if self.drink_type == CANONICAL_TYPE else 0

    @property
    def total_unit(self) -> str:
        """The unit a year's worth of drinking is read in."""
        return "Std Av" if self.drink_type == CANONICAL_TYPE else "L"

    def display_to_total(self, value: float) -> float:
        """A shown amount as a yearly total: millilitres add up to litres, but
        Std Av is a count, so a thousand of them is not a litre of anything."""
        if self.drink_type == CANONICAL_TYPE:
            return value

        return value / 1000

    def stdav_to_display(self, stdav: float) -> float:
        """Std Av in the unit it is shown in — the rule ``DrinkQuantity.value``
        applies, so a chart and a card never disagree about what a number means.

        Std Av is canonical and shown as typed; converting it would report the
        10 ml of pure alcohol one Std Av contains, ten times the number a user
        entered and ten times the Drink Target it is read against.
        """
        if self.drink_type == CANONICAL_TYPE:
            return stdav

        return self.stdav_to_ml(stdav)

    def stdav_to_total(self, stdav: float) -> float:
        """Std Av in the unit a yearly total is read in."""
        return self.display_to_total(self.stdav_to_display(stdav))

    @staticmethod
    def stdav_to_alcohol(stdav: float) -> float:
        # one stdav = 10g pure alcohol (100%)
        return stdav * 0.01

    def max_bottles_per_year(self, year: int, max_stdav: float) -> float:
        days = ydays(year)
        return (max_stdav * days) / self._ratio.stdav
