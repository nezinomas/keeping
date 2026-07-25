from dataclasses import dataclass

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _

from .drinks_options import MAX_BOTTLES, DrinkConverter

CANONICAL_TYPE = "stdav"


@dataclass(frozen=True)
class DrinkQuantity:
    """A drink amount: canonical in Std Av, aware of the unit it is shown in.

    Std Av is the canonical unit, so an amount of that drink type is entered,
    stored and displayed as the same number — nothing is converted for it.

    Every other drink type is entered and displayed either as a volume in
    millilitres or as a count of pieces. ``MAX_BOTTLES`` is the rule that
    decides which one a typed number meant: nobody drinks more than 20 bottles
    in a day, so a larger number can only have been millilitres. Which way a
    stored record was entered is what ``Drink.converted_from_ml`` remembers.
    """

    stdav: float
    drink_type: str
    is_volume: bool = False

    # -- constructors ------------------------------------------------------
    @classmethod
    def from_input(cls, value: float, drink_type: str) -> "DrinkQuantity":
        """Interpret a number typed into the quantity field."""
        if drink_type == CANONICAL_TYPE:
            return cls(stdav=value, drink_type=drink_type)

        converter = DrinkConverter(drink_type)

        if value > MAX_BOTTLES:
            return cls(converter.ml_to_stdav(value), drink_type, is_volume=True)

        return cls(value / converter.ratio, drink_type)

    @classmethod
    def from_volume(cls, ml: float, drink_type: str) -> "DrinkQuantity":
        """Interpret a number that is always a volume, never a count."""
        if drink_type == CANONICAL_TYPE:
            return cls(stdav=ml, drink_type=drink_type)

        converter = DrinkConverter(drink_type)

        return cls(converter.ml_to_stdav(ml), drink_type, is_volume=True)

    @classmethod
    def from_stdav(
        cls, stdav: float, drink_type: str, *, is_volume: bool = False
    ) -> "DrinkQuantity":
        """Rebuild an amount from a stored row."""
        if drink_type == CANONICAL_TYPE:
            is_volume = False

        return cls(stdav=stdav, drink_type=drink_type, is_volume=is_volume)

    # -- readers -----------------------------------------------------------
    @property
    def value(self) -> float:
        """The amount in the unit it is shown in."""
        if self.drink_type == CANONICAL_TYPE:
            return self.stdav

        converter = DrinkConverter(self.drink_type)

        if self.is_volume:
            return converter.stdav_to_ml(self.stdav)

        return self.stdav * converter.ratio

    @property
    def unit_label(self) -> str:
        return _("ml") if self.is_volume else _("pcs")

    @property
    def decimal_places(self) -> int:
        return 0 if self.is_volume else 1

    @property
    def display(self) -> str:
        """Localized ``value`` and unit, e.g. ``500 ml`` or ``1,0 pcs``."""
        number = floatformat(self.value, f"{self.decimal_places}g")

        return f"{number} {self.unit_label}"
