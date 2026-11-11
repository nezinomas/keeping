from datetime import date

from ...core.lib.year_boundary import YearBoundary


def average(qs, today: date) -> list[float | None]:
    """Yearly sums as monthly means, a running year divided by the months of it
    that have happened. A Coming year has had none, so its mean is Highcharts'
    `null` gap."""
    return [_monthly_mean(r["sum"], YearBoundary(r["year"], today)) for r in qs]


def _monthly_mean(total: int, boundary: YearBoundary) -> float | None:
    if boundary.is_coming:
        return None

    return float(total) / boundary.months_elapsed
