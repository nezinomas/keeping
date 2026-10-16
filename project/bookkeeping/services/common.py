from datetime import date

from ...core.lib.year_boundary import YearBoundary


def average(qs, today: date):
    """Yearly sums as monthly means, a running year divided by the months of it
    that have happened."""
    return [float(r["sum"]) / YearBoundary(r["year"], today).end_date.month for r in qs]
