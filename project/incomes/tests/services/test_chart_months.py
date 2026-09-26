from datetime import date

from ....core.lib.year_boundary import YearBoundary
from ...services.chart_months import ChartMonths

RUNNING = YearBoundary(year=2026, today=date(2026, 9, 15))
FINISHED = YearBoundary(year=2025, today=date(2026, 9, 15))


def _chart(year=(), last_year=(), boundary=RUNNING):
    return ChartMonths.build(list(year), list(last_year), boundary)


def _data(chart):
    return {series["name"]: series["data"] for series in chart["series"]}


def test_categories_are_the_twelve_months():
    categories = _chart()["categories"]

    assert len(categories) == 12
    assert categories[0] == "Sau"


def test_last_year_comes_first_so_the_year_is_drawn_darkest():
    assert list(_data(_chart())) == ["2025", "2026"]


def test_a_running_year_stops_at_the_boundary_month():
    chart = _chart(year=[{"date": date(2026, 1, 1), "sum": 100}])

    assert len(_data(chart)["2026"]) == 9


def test_last_year_stops_at_the_same_month():
    chart = _chart(last_year=[{"date": date(2025, 12, 1), "sum": 100}])

    assert len(_data(chart)["2025"]) == 9


def test_a_finished_year_has_twelve_months():
    assert len(_data(_chart(boundary=FINISHED))["2025"]) == 12


def test_amounts_are_euro_and_a_month_without_incomes_is_zero():
    chart = _chart(
        year=[
            {"date": date(2026, 1, 1), "sum": 123_400},
            {"date": date(2026, 3, 1), "sum": 50},
        ]
    )

    assert _data(chart)["2026"][:4] == [1234.0, 0.0, 0.5, 0.0]
