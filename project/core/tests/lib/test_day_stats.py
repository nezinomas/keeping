from datetime import date

import pytest

from ...lib.day_stats import NoPastRecord, PastRecord, Stats


def in_year(rows, year):
    return [row for row in rows if row["date"].year == year]


@pytest.fixture(name="data")
def fixture_data():
    return [
        {"date": date(1999, 12, 3), "qty": 1.0},
        {"date": date(1999, 2, 1), "qty": 2.0},
        {"date": date(1999, 1, 15), "qty": 2.0},
        {"date": date(1999, 1, 8), "qty": 1.0},
        {"date": date(2000, 1, 8), "qty": 1.0},
    ]


@pytest.mark.parametrize(
    "years, expect",
    [
        pytest.param(
            (1999,),
            [2, 0, 0, 0, 4, 0, 0],
            id="one_year",
        ),
        pytest.param(
            (1999, 2000),
            [2, 0, 0, 0, 4, 1, 0],
            id="all_years",
        ),
        pytest.param((), [0] * 7, id="empty"),
    ],
)
def test_stats_weekdays_aggregation(data, years, expect):
    rows = [row for row in data if row["date"].year in years]

    actual = Stats(data=rows).weekdays_stats()

    assert actual == [{"weekday": day, "count": n} for day, n in enumerate(expect)]


@pytest.mark.parametrize(
    "years, expect",
    [
        pytest.param(
            (1999,),
            [3.0, 2.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1.0],
            id="one_year",
        ),
        pytest.param((), [0.0] * 12, id="empty"),
    ],
)
def test_stats_months_aggregation(data, years, expect):
    rows = [row for row in data if row["date"].year in years]

    assert Stats(data=rows).months_stats() == expect


@pytest.mark.parametrize(
    "earlier, extra, expect",
    [
        pytest.param(
            NoPastRecord(),
            [{"date": date(1999, 2, 2), "qty": 1.0}],
            {
                date(1999, 1, 8): 7,
                date(1999, 2, 2): 1,
                date(1999, 12, 3): 304,
            },
            id="from_the_record_before",
        ),
        pytest.param(
            PastRecord(date(1998, 1, 1)),
            [],
            {date(1999, 1, 8): 372},
            id="with_an_earlier_record",
        ),
    ],
)
def test_stats_gap_by_date(data, earlier, extra, expect):
    actual = Stats(data=in_year(data, 1999) + extra, earlier=earlier).gap_by_date()

    assert expect.items() <= actual.items()


def test_stats_gap_by_date_empty():
    assert Stats(data=[]).gap_by_date() == {}
