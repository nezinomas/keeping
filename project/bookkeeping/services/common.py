from datetime import date

from ...core.lib.year_boundary import YearBoundary


def average(qs, today: date | None = None):
    """Yearly sums as monthly means, a running year divided by the months of it
    that have happened."""
    today = today or date.today()

    return [
        float(r["sum"]) / YearBoundary.for_year(r["year"], today).end_date.month
        for r in qs
    ]
