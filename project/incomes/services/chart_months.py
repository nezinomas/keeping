from collections.abc import Sequence
from dataclasses import dataclass

from ...core.lib.convert_price import int_cents_to_float
from ...core.lib.translation import month_abbr
from ...core.lib.year_boundary import YearBoundary


@dataclass(frozen=True)
class ChartMonths:
    year: Sequence[dict]
    last_year: Sequence[dict]
    boundary: YearBoundary

    @classmethod
    def build(
        cls, year: Sequence[dict], last_year: Sequence[dict], boundary: YearBoundary
    ) -> dict:
        return cls(year, last_year, boundary)._chart()

    def _chart(self) -> dict:
        year = self.boundary.year

        return {
            "categories": [month_abbr(month) for month in range(1, 13)],
            "series": [
                {"name": str(year - 1), "data": self._months(self.last_year)},
                {"name": str(year), "data": self._months(self.year)},
            ],
        }

    def _months(self, rows: Sequence[dict]) -> list[float]:
        # last year stops where this year does, or the comparison lies
        months = self.boundary.end_date.month
        sums = [0.0] * months

        for row in rows:
            if row["date"].month <= months:
                sums[row["date"].month - 1] = int_cents_to_float(row["sum"])

        return sums
