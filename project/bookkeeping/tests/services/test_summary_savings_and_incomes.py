from datetime import date
from types import SimpleNamespace
from typing import cast

import pytest

from ...services.summary_savings_and_incomes import Data, Service

TODAY = date(2001, 1, 1)

I99, I00, I01 = (
    {"year": 1999, "sum": 10},
    {"year": 2000, "sum": 11},
    {"year": 2001, "sum": 12},
)
S99, S00, S01 = (
    {"year": 1999, "sum": 20},
    {"year": 2000, "sum": 21},
    {"year": 2001, "sum": 22},
)


def _chart_data(user, incomes, savings):
    data = cast(Data, SimpleNamespace(incomes=incomes, savings=savings))
    return Service(user, data, TODAY).chart_data()


@pytest.mark.django_db
def test_chart_data_categories(main_user):
    actual = _chart_data(main_user, [], [])["categories"]

    assert actual == [1999, 2000, 2001]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "incomes, savings, key, expect",
    [
        pytest.param([I99, I00, I01], [], "incomes", [10, 11, 12], id="incomes"),
        pytest.param([I99, I01], [], "incomes", [10, 0, 12], id="incomes_no_record"),
        pytest.param(
            [I99, I00, I01], [S99, S00, S01], "savings", [20, 21, 22], id="savings"
        ),
        pytest.param(
            [I99, I00, I01], [S99, S01], "savings", [20, 0, 22], id="savings_no_record"
        ),
        pytest.param(
            [I99, I00, I01],
            [S99, S00, S01],
            "percents",
            pytest.approx([200, 190.91, 183.33], 0.01),
            id="percents",
        ),
        pytest.param(
            [I99, I01], [S99, S00], "percents", [200, 0, 0], id="percents_no_record"
        ),
    ],
)
def test_chart_data(main_user, incomes, savings, key, expect):
    actual = _chart_data(main_user, incomes, savings)[key]

    assert actual == expect
