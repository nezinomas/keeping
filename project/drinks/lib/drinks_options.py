from dataclasses import dataclass

from ...core.lib.date import ydays
from .drink_types import DrinkType

MAX_BOTTLES = 20


@dataclass(frozen=True)
class DrinkTypeSpec:
    stdav: float  # how many Std Av in one unit
    ml: float  # what one unit is, in millilitres
    is_canonical: bool = False
    display_unit: str = "ml"
    total_unit: str = "L"
    display_decimals: int = 0


DRINK_SPECS: dict[str, DrinkTypeSpec] = {
    DrinkType.BEER: DrinkTypeSpec(stdav=2.5, ml=500),
    DrinkType.WINE: DrinkTypeSpec(stdav=8, ml=750),
    DrinkType.VODKA: DrinkTypeSpec(stdav=40, ml=1000),
    DrinkType.STDAV: DrinkTypeSpec(
        stdav=1,
        ml=10,
        is_canonical=True,
        display_unit="Std Av",
        total_unit="Std Av",
        display_decimals=1,  # a whole ml is precise enough, a Std Av is not
    ),
}

if _undeclared := set(DrinkType.values) - set(DRINK_SPECS):
    raise RuntimeError(f"drink types without a spec: {sorted(_undeclared)}")

# for data that predates the choices, not for a declared type left out above.
# Std Av's ratios only: an unrecognised type is not the canonical one.
_CANONICAL_SPEC = DRINK_SPECS[DrinkType.STDAV]
_LEGACY_SPEC = DrinkTypeSpec(stdav=_CANONICAL_SPEC.stdav, ml=_CANONICAL_SPEC.ml)


class DrinkConverter:
    def __init__(self, drink_type: str):
        self.drink_type = drink_type
        self._spec = DRINK_SPECS.get(drink_type, _LEGACY_SPEC)

    @property
    def is_canonical(self) -> bool:
        return self._spec.is_canonical

    @property
    def ratio(self) -> float:
        return 1 / self._spec.stdav

    @property
    def stdav_per_unit(self) -> float:
        return self._spec.stdav

    def convert_qty(self, qty: float, to_type: str) -> float:
        target = DRINK_SPECS.get(to_type, _LEGACY_SPEC)
        return (qty * self._spec.stdav) / target.stdav

    def ml_to_stdav(self, ml: int | float) -> float:
        return (ml * self._spec.stdav) / self._spec.ml

    def stdav_to_ml(self, stdav: float) -> float:
        return (stdav * self._spec.ml) / self._spec.stdav

    @property
    def display_unit(self) -> str:
        """The unit an amount of this drink type is read in."""
        return self._spec.display_unit

    @property
    def figure_unit(self) -> str:
        # a Std Av figure is drawn unitless and names its unit in the explanation
        return "" if self._spec.is_canonical else self._spec.display_unit

    @property
    def display_decimals(self) -> int:
        return self._spec.display_decimals

    @property
    def total_unit(self) -> str:
        """The unit a year's worth of drinking is read in."""
        return self._spec.total_unit

    def display_to_total(self, value: float) -> float:
        """A shown amount as a yearly total: millilitres add up to litres, but
        Std Av is a count, so a thousand of them is not a litre of anything."""
        if self._spec.is_canonical:
            return value

        return value / 1000

    def stdav_to_display(self, stdav: float) -> float:
        if self._spec.is_canonical:
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
        return (max_stdav * days) / self._spec.stdav
