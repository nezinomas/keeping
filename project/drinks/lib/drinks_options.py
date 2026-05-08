from dataclasses import dataclass
from enum import Enum

from ...core.lib.date import ydays

MAX_BOTTLES = 20


@dataclass(frozen=True)
class _Ratio:
    stdav: float
    ml: float


class DrinkRatio(Enum):
    beer  = _Ratio(stdav=2.5,  ml=500)   # 500ml  -> 2.5 std_av
    wine  = _Ratio(stdav=8,    ml=750)   # 750ml  -> 8   std_av
    vodka = _Ratio(stdav=40,   ml=1000)  # 1000ml -> 40  std_av
    stdav = _Ratio(stdav=1,    ml=10)    # 10ml   -> 1   std_av

    @classmethod
    def from_str(cls, name: str) -> "DrinkRatio":
        try:
            return cls[name]
        except KeyError:
            return cls.stdav


class DrinksOptions:
    def __init__(self, drink_type: str):
        self.drink_type = drink_type
        self._ratio = DrinkRatio.from_str(drink_type).value

    @property
    def ratio(self) -> float:
        return 1 / self._ratio.stdav

    @property
    def stdav(self) -> float:
        return self._ratio.stdav

    def convert(self, qty: float, drink_type: str) -> float:
        target = DrinkRatio.from_str(drink_type).value
        return (qty * self._ratio.stdav) / target.stdav

    def ml_to_stdav(self, ml: int | float) -> float:
        return (ml * self._ratio.stdav) / self._ratio.ml

    def stdav_to_ml(self, stdav: float) -> float:
        return (stdav * self._ratio.ml) / self._ratio.stdav

    @staticmethod
    def stdav_to_alcohol(stdav: float) -> float:
        # one stdav = 10g pure alkohol (100%)
        return stdav * 0.01

    def stdav_to_bottles(self, year: int, max_stdav: float) -> float:
        days = ydays(year)
        return (max_stdav * days) / self._ratio.stdav
