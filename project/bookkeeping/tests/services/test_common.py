import pytest
import time_machine

from ...services import common


@pytest.mark.parametrize(
    "today, expect",
    [
        pytest.param("2000-2-5", [6], id="average_current_year"),
        pytest.param("2001-2-5", [1], id="average_past_year"),
    ],
)
def test_average_of_a_year_by_months_it_has_had(today, expect):
    qs = [{"year": 2000, "sum": 12}]

    with time_machine.travel(today):
        actual = common.average(qs)

    assert actual == expect


@time_machine.travel("2000-2-5")
def test_average():
    qs = [{"year": 1999, "sum": 12}, {"year": 2000, "sum": 12}]

    actual = common.average(qs)

    assert actual == [1, 6]
