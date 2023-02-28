import pytest
import time_machine

from ..services import common as T

pytestmark = pytest.mark.django_db


@time_machine.travel("2000-2-5")
def test_average_current_year():
    qs = [{"year": 2000, "sum": 12}]

    actual = T.average(qs)

    assert actual == [6]


@time_machine.travel("2001-2-5")
def test_average_past_year():
    qs = [{"year": 2000, "sum": 12}]

    actual = T.average(qs)

    assert actual == [1]


@time_machine.travel("2000-2-5")
def test_average():
    qs = [{"year": 1999, "sum": 12}, {"year": 2000, "sum": 12}]

    actual = T.average(qs)

    assert actual == [1, 6]
