from datetime import date

import pytest

from ...services import common


@pytest.mark.parametrize(
    "today, expect",
    [
        pytest.param(date(2000, 2, 5), [6], id="average_current_year"),
        pytest.param(date(2001, 2, 5), [1], id="average_past_year"),
    ],
)
def test_average_of_a_year_by_months_it_has_had(today, expect):
    qs = [{"year": 2000, "sum": 12}]

    actual = common.average(qs, today)

    assert actual == expect


def test_average():
    qs = [{"year": 1999, "sum": 12}, {"year": 2000, "sum": 12}]

    actual = common.average(qs, date(2000, 2, 5))

    assert actual == [1, 6]
