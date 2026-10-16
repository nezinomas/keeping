from datetime import date

import pytest

from ...services import common


@pytest.mark.parametrize(
    "qs, today, expect",
    [
        pytest.param(
            [{"year": 2000, "sum": 12}],
            date(2000, 2, 5),
            [6],
            id="average_current_year",
        ),
        pytest.param(
            [{"year": 2000, "sum": 12}], date(2001, 2, 5), [1], id="average_past_year"
        ),
        pytest.param(
            [{"year": 1999, "sum": 12}, {"year": 2000, "sum": 12}],
            date(2000, 2, 5),
            [1, 6],
            id="average_past_and_current_year",
        ),
    ],
)
def test_average_of_a_year_by_months_it_has_had(qs, today, expect):
    actual = common.average(qs, today)

    assert actual == expect
