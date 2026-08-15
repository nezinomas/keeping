from dataclasses import dataclass

from django.template.defaultfilters import floatformat
from django.utils.translation import gettext as _

from .drinks_options import MAX_BOTTLES, DrinkConverter


@dataclass(frozen=True)
class DrinkQuantity:
    stdav: float
    drink_type: str
    is_volume: bool = False

    @classmethod
    def from_input(cls, value: float, drink_type: str) -> "DrinkQuantity":
        """Interpret a number typed into the quantity field."""
        converter = DrinkConverter(drink_type)

        if converter.is_canonical:
            return cls(stdav=value, drink_type=drink_type)

        if value > MAX_BOTTLES:
            return cls(converter.ml_to_stdav(value), drink_type, is_volume=True)

        return cls(converter.servings_to_stdav(value), drink_type)

    @classmethod
    def from_volume(cls, ml: float, drink_type: str) -> "DrinkQuantity":
        """Interpret a number that is always a volume, never a count."""
        converter = DrinkConverter(drink_type)

        if converter.is_canonical:
            return cls(stdav=ml, drink_type=drink_type)

        return cls(converter.ml_to_stdav(ml), drink_type, is_volume=True)

    @classmethod
    def from_stdav(
        cls, stdav: float, drink_type: str, *, is_volume: bool = False
    ) -> "DrinkQuantity":
        """Rebuild an amount from a stored row."""
        if DrinkConverter(drink_type).is_canonical:
            is_volume = False

        return cls(stdav=stdav, drink_type=drink_type, is_volume=is_volume)

    @property
    def value(self) -> float:
        """The amount in the unit it is shown in."""
        converter = DrinkConverter(self.drink_type)

        if converter.is_canonical:
            return self.stdav

        if self.is_volume:
            return converter.stdav_to_ml(self.stdav)

        return converter.stdav_to_servings(self.stdav)

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
